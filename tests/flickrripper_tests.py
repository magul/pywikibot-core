"""Tests for the Flickrripper."""
#
# (C) Pywikibot team, 2008-2015
#
# Distributed under the terms of the MIT License

from tests.aspects import unittest
import scripts.flickrripper


class FlickrripperTests(unittest.TestCase):

    """Test flickrripper."""

    def test_Autnomous_mode(self):
        """Test to check if autonomous mode works properly."""
        def newDuplicateChecker():
                return []
        oldDuplicateChecker = flickrripper.findDuplicateImages
        flickrripper.findDuplicateImages = newDuplicateChecker
        # what link to Use to upload ?
        var = flickrripper.processPhoto(flickr=None, photo_id=u'', flickrreview=False, reviewer=u'',
                                        override=u'', addCategory=u'', removeCategories=False,
                                        autonomous=True)
        self.assertEqual(var, 1)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
