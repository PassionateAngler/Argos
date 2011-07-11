# -*- coding: UTF-8 -*-
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404
from django.views.generic import list_detail
from moviemaker.models import Camera, MovieCacheFile, ImageFile, KeyFrame
from moviemaker.forms import CameraSearch

def camera_moviecache(request,slug):
    from django.db import connection
    connection.queries = []
    camera = get_object_or_404(Camera,slug__iexact=slug)    
    return list_detail.object_list(
        request,
        queryset =\
            MovieCacheFile.objects.select_related().filter(camera=camera).order_by('_start'),
        template_name = 'camera/movies_by_camera.html',
        template_object_name = 'movie',
        extra_context = {'camera': camera, 'queries':connection.queries}
    )

def camera_search(request,slug):
    import simplejson as json
    from pytz import timezone
    from datetime import datetime, timedelta
    from moviemaker.settings import MOVIECACHE_URL ,MEDIA_LOGGER, ARGOS_LOGGER,\
        MAX_SLICE_NUMBER
    from moviemaker.bin.functions import create_tmpdir, create_movie
    DATE_FORMAT = '%Y-%m-%d %H:%M'
    DELTA = timedelta(minutes=5)
    camera = get_object_or_404(Camera,slug__iexact=slug)    
    tz = camera.localization.timezone
    if request.GET:
        form = CameraSearch(request.GET)
        movie = None
        if form.is_valid():
            #helper function  witch looks for closest movie from start or end date
            def select_closest(cl_slices,start=None,end=None):
                if start:
                    cl_keyframes = KeyFrame.objects.filter(\
                        imagefile__camera__name=camera,\
                        imagefile___date__lt=start)
                elif end:
                    cl_keyframes = KeyFrame.objects.filter(\
                        imagefile__camera__name=camera,\
                        imagefile___date__gt=end)

                if cl_keyframes:
                    if start:
                        cl_frame = cl_keyframes.select_related().order_by('-imagefile___date')[0]
                    elif end:
                        cl_frame = cl_keyframes.select_related().order_by('imagefile___date')[0]

                    slice_id = cl_frame.slice_id
                    for n in range(MAX_SLICE_NUMBER):
                        if cl_frame.slice_id - n < 0:
                            break
                        if start:
                            slice_id = cl_frame.slice_id - n
                        elif end:
                            slice_id = cl_frame.slice_id + n
                        
                        slice = cl_keyframes.filter( 
                            moviecachefile=cl_frame.moviecachefile,
                            slice_id = slice_id 
                        )
                        cl_slices.append(
                            { 
                                'first':slice[0].imagefile.date\
                                        .astimezone(tz).strftime(DATE_FORMAT),
                                'last':slice[len(slice) - 1].imagefile.date\
                                        .astimezone(tz).strftime(DATE_FORMAT),
                                'len':len(slice)
                            }
                        )

            def render_closest():
                cl_slices = []
                select_closest(cl_slices,start)
                select_closest(cl_slices,None,end)
                return render(request, 'camera/camera_movie.html', {'camera':camera,\
                        'form':form,'cl_slices':cl_slices})

            LOG_NO_MOVIE_FOUND = lambda slug,s,e: ARGOS_LOGGER.debug(\
                "Camera %s: no movie file in cache for range %s to %s"\
                %(\
                    slug,\
                    s,\
                    e\
                )\
            )

            cd = form.cleaned_data
            cd['start'] = tz.localize(cd['start']).astimezone(timezone('UTC'))
            start = cd['start'] - DELTA
            #cd['end'] = tz.localize(cd['end']).astimezone(timezone('UTC'))
            end = cd['start'] + DELTA \
                    + timedelta(seconds=MovieCacheFile.MAX_SLICE_DIST - 1)
            #searching for movie
            moviefile_set = MovieCacheFile.objects.filter(\
                camera = camera,\
                _start__lte = end,\
                _end__gte = start
            )

            if not moviefile_set:
                #no movie in cache
                movie = camera.create_moviecachefile(start,end)
                #no frames to render
                if not movie:
                    LOG_NO_MOVIE_FOUND(camera.slug, start, end)
                    return render_closest()
            elif len(moviefile_set)>1:
                #more than one movie contains given range
                #we need to find which file cointains whole range
                for video in moviefile_set:
                    if video.start <= start + DELTA \
                    and video.end >= end - DELTA:
                        movie = video 
                        break
                #or create it
                if not movie:
                    movie = camera.create_moviecachefile(start,end)
                    #no frames to render
                    #TODO: check is it possible?!
                    if not movie:
                        LOG_NO_MOVIE_FOUND(camera.slug, start, end)
                        return render_closest()
            else:
                #only one movie matching boundry
                movie = moviefile_set.get()

            #find start keyframe
            frames = KeyFrame.objects.select_related().filter(\
                moviecachefile = movie,
                imagefile___date__gte = start,\
                imagefile___date__lte = end
            )

            if not frames:
                #no frames found
                LOG_NO_MOVIE_FOUND(camera.slug, start, end)
                return render_closest()

            start_cc = frames[0].position
            end_cc = frames[len(frames)-1].position
            
            return render(request, 'camera/camera_movie.html', {'camera':camera,\
                    'form':form,'movie':movie,'start':frames[0].position,\
                    'frames':frames,'start_cc':start_cc,'end_cc':end_cc,\
                    'cuepoints':json.dumps([\
                        t*1000 for t in range(frames.count())\
                        ]), 'moviecache_url': MOVIECACHE_URL})
    else:
        form = CameraSearch()

    return render(request, 'camera/camera_search.html', {'camera':camera,\
            'form':form})

def moviecachefile_subtitles(request, movie_id, start_cc, end_cc):
    mcfile = get_object_or_404(MovieCacheFile,id=movie_id)    
    start_cc = int(start_cc)
    end_cc = int(end_cc)
    if start_cc>end_cc or start_cc<0 or end_cc<0:
        raise Http404

    ttxml = mcfile.create_subs_tt(start_cc,end_cc)
    return HttpResponse(ttxml,mimetype='text/xml')
