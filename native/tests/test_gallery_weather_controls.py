"""Typing weather in the shipped Gallery starts from its controls alone.

Choosing a weather style (or changing any cursor or weather field) takes effect at once: typing in the prompt then
raises weather events without pressing "Apply cursor and weather".
"""
import os
import unittest
from pathlib import Path

NATIVE = Path(__file__).resolve().parents[1]
PAGE = NATIVE / 'Nocturne-RC4-Source-Build.html'


class GalleryWeatherControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not PAGE.is_file():
            raise unittest.SkipTest('build the Gallery first (sh build-native.sh)')
        from playwright.sync_api import sync_playwright
        cls.playwright = sync_playwright().start()
        executable = os.environ.get('CHROMIUM')
        cls.browser = cls.playwright.chromium.launch(**({'executable_path': executable} if executable else {}))

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def page(self):
        page = self.browser.new_page(viewport={'width': 1680, 'height': 1000})
        self.addCleanup(page.close)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        self.addCleanup(lambda: self.assertEqual(errors, []))
        page.goto(PAGE.as_uri())
        page.wait_for_function('window.nativeLab && window.nativeView')
        page.evaluate("nativeLab.load(nativeLab.recipes.find(r => r.id === 'silk'))")
        return page

    def weather(self, page):
        return page.evaluate('nativeLab.scene.info().prompt.appearance.weather')

    def test_choosing_a_style_applies_it_without_the_apply_button(self):
        page = self.page()
        page.select_option('#prompt-weather-style', 'embers')
        self.assertEqual(self.weather(page)['style'], 'embers')
        page.click('#draft')
        page.keyboard.type('weather', delay=40)
        page.wait_for_timeout(100)
        self.assertGreater(self.weather(page)['eventSerial'], 0)

    def test_numeric_fields_apply_on_change(self):
        page = self.page()
        page.select_option('#prompt-weather-style', 'snow')
        page.fill('#prompt-weather-intensity', '0.9')
        page.dispatch_event('#prompt-weather-intensity', 'change')
        weather = self.weather(page)
        self.assertEqual(weather['style'], 'snow')
        self.assertAlmostEqual(weather['intensity'], 0.9)


if __name__ == '__main__':
    unittest.main()
