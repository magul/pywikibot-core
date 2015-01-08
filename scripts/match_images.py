#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Program to match two images based on histograms.

Usage:
match_images.py ImageA ImageB
It is essential to provide two images to work on.
example. - match_images.py ImageA.jpg ImageB.jpg

&params;

Furthermore, the following command line parameters are supported:

-otherfamily        Mentioned family with this parameter will be preferred for
                    fetching file usage details instead of the default
                    family retrieved from user-congig.py script.

-otherlang          Mentioned lang with this parameter will be preferred for
                    fetching file usage details instead of the default
                    mylang retrieved from user-congig.py script.

This is just a first version so that other people can play around with it.
Expect the code to change a lot!
"""
#
# (c) Multichill, 2009
# (c) Pywikibot team, 2009-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import division
__version__ = '$Id$'


import io
from PIL import Image

import pywikibot
from pywikibot.comms import http


def match_file_pages(file_page_a, file_page_b):
    """Match two images based on FilePage objects.

    @param file_page_a: file page of the first image
    @type file_page_a: pywikibot.FilePage
    @param file_page_b: file page of the second image
    @type file_page_b: pywikibot.FilePage
    @return: whether the images are the same
    @rtype: bool
    """
    imageA = get_image_from_file_page(file_page_a)
    imageB = get_image_from_file_page(file_page_b)

    (imA_width, imA_height) = imageA.size
    (imB_width, imB_height) = imageB.size

    imageB = imageB.resize((imA_width, imA_height))

    imageA_topleft = imageA.crop((0, 0, imA_width // 2, imA_height // 2))
    imageB_topleft = imageB.crop((0, 0, imA_width // 2, imA_height // 2))

    imageA_topright = imageA.crop((imA_width // 2, 0, imA_width,
                                  imA_height // 2))
    imageB_topright = imageB.crop((imA_width // 2, 0, imA_width,
                                  imA_height // 2))

    imageA_bottomleft = imageA.crop((0, imA_height // 2, imA_width // 2,
                                     imA_height))
    imageB_bottomleft = imageB.crop((0, imA_height // 2, imA_width // 2,
                                     imA_height))

    imageA_bottomright = imageA.crop((imA_width // 2, imA_height // 2,
                                      imA_width, imA_height))
    imageB_bottomright = imageB.crop((imA_width // 2, imA_height // 2,
                                      imA_width, imA_height))

    imageA_center = imageA.crop((int(imA_width * 0.25), int(imA_height * 0.25),
                                int(imA_width * 0.75), int(imA_height * 0.75)))
    imageB_center = imageB.crop((int(imA_width * 0.25), int(imA_height * 0.25),
                                int(imA_width * 0.75), int(imA_height * 0.75)))

    wholeScore = match_images(imageA, imageB)
    topleftScore = match_images(imageA_topleft, imageB_topleft)
    toprightScore = match_images(imageA_topright, imageB_topright)
    bottomleftScore = match_images(imageA_bottomleft, imageB_bottomleft)
    bottomrightScore = match_images(imageA_bottomright, imageB_bottomright)
    centerScore = match_images(imageA_center, imageB_center)
    averageScore = (wholeScore + topleftScore + toprightScore +
                    bottomleftScore + bottomrightScore + centerScore) / 6

    print (u'Whole image           ' + str(wholeScore))
    print (u'Top left of image     ' + str(topleftScore))
    print (u'Top right of image    ' + str(toprightScore))
    print (u'Bottom left of image  ' + str(bottomleftScore))
    print (u'Bottom right of image ' + str(bottomrightScore))
    print (u'Center of image       ' + str(centerScore))
    print (u'                      -------------')
    print (u'Average               ' + str(averageScore))

    # Hard coded at 80%, change this later on.
    if averageScore > 0.8:
        print (u'We have a match!')
        return True
    else:
        print (u'Not the same.')
        return False


def get_image_from_file_page(file_page):
    """ Get the image object to work on based on a FilePage object. """
    image_url_opener = http.fetch(file_page.fileUrl())
    image_buffer = io.BytesIO(image_url_opener.raw[:])
    image = Image.open(image_buffer)
    return image


def match_images(image_a, image_b):
    """ Match two image objects. Return the ratio of pixels that match. """
    histogram_a = image_a.histogram()
    histogram_b = image_b.histogram()

    total_match = 0
    total_pixels = 0

    if len(histogram_a) != len(histogram_b):
        return 0

    for i in range(0, len(histogram_a)):
        total_match += min(histogram_a[i], histogram_b[i])
        total_pixels += max(histogram_a[i], histogram_b[i])

    if total_pixels == 0:
        return 0

    return total_match / total_pixels * 100


def main(*args):
    """ Extract file page information of images to work on and initiate matching. """
    images = []
    other_family = None
    other_lang = None

    # Read commandline parameters.
    local_args = pywikibot.handle_args(args)

    for arg in local_args:
        if arg.startswith('-otherfamily:'):
            if len(arg) == len('-otherfamily:'):
                other_family = pywikibot.input(u'What family do you want to use?')
            else:
                other_family = arg[len('-otherfamily:'):]
        elif arg.startswith('-otherlang:'):
            if len(arg) == len('-otherlang:'):
                other_lang = pywikibot.input(u'What language do you want to use?')
            else:
                other_lang = arg[len('otherlang:'):]
        else:
            images.append(arg)

    if len(images) != 2:
        pywikibot.showHelp()
        pywikibot.error('Require two images to work on.')
        return

    file_page_a = pywikibot.FilePage(pywikibot.Site(), images[0])
    if other_lang:
        if other_family:
            other_args = (other_lang, other_family)
        else:
            other_args = (other_lang,)
    else:
        other_args = tuple()
    file_page_b = pywikibot.FilePage(pywikibot.Site(*other_args), images[1])

    match_file_pages(file_page_a, file_page_b)


if __name__ == "__main__":
    main()
