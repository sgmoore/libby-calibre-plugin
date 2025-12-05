from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import truncate_for_display 
else :    
    from calibre_plugins.overdrive_libby.models import truncate_for_display 

from all import RunnableTests

class TruncateTests(RunnableTests):

    # This test has been disabled because it always failed.
    # Perhaps this test was written when the truncation routine always returned a predicable number of characters
    # but it looks to me like the calibre routine measures the actual text and hence the number of characters 
    # that 'fit' will depend on the font used as well as the text 

    # def test_truncate_for_display(self):
    
    #     self.assertEqual(
    #         "Ipsum debitis dignissimo…",
    #         truncate_for_display("Ipsum debitis dignissimos aspernatur."),
    #     )
    #     self.assertEqual(
    #         "Ipsum debitis dignissimo…",
    #         truncate_for_display("Ipsum debitis dignissimos aspernatur.", width=-100),
    #     )
    #     self.assertEqual(
    #         "Ipsum debitis dignissimo…",
    #         truncate_for_display(
    #             "Ipsum debitis dignissimos aspernatur.", text_length=-1
    #         ),
    #     )
    #     self.assertEqual(
    #         "Ipsum debitis d…",
    #         truncate_for_display(
    #             "Ipsum debitis dignissimos aspernatur.", text_length=20
    #         ),
    #     )

    def test_truncate_short(self):
        original = "Ipsum." 
        t1 = truncate_for_display(original)
        self.assertEqual( t1, original)
 
    def test_truncate_long(self):

        # Normally this string does not need to be truncated.
        ipsum = "Ipsum debitis dignissimos aspernatur." 
        t = truncate_for_display(ipsum)
        
        self.assertEqual(t, ipsum, "Normally this would fit without truncating")

        doubled = ipsum+ipsum 
        t2 = truncate_for_display(doubled, 30)
        self.assertNotEqual(t2, doubled, "Doubled would normally NOT fit without truncating")

   
        t4 = truncate_for_display(doubled, 200)
        self.assertEqual(t4, doubled, "Should fit in 200 characters")

        t4 = truncate_for_display(doubled, width = 1000)
        self.assertEqual(t4, doubled, "Should fit in 100 width ")

        # Capital W's are much wider than normal characters, so even though it has the
        # same number of characters as ipsum, it normally would not fit.

        w = "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW" 
        self.assertEqual(len(w), len(ipsum))
        t = truncate_for_display(w)

        self.assertNotEqual(t, w, "Normally this would NOT fit without truncating")

        ellipsis = '…' # Note this is one character not three dots.

        self.assertEqual( t, w[0 : len(t)-1] + ellipsis)

    
        

      

if __name__ == "__main__":
    TruncateTests.run_tests()
