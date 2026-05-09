from bs4 import BeautifulSoup
from flask import redirect, render_template, session
from functools import wraps 
import re

def extract_urls(text):
    pattern = r'(https?://[^\s]+)'
    return re.findall(pattern, text)

def run_test(name, text):
    print(f"\n--- {name} ---")
    print("Input:")
    print(text)
    print("\nExtracted URLs:")
    urls = extract_urls(text)
    for u in urls:
        print(" -", u)
    print("-------------------------")


if __name__ == "__main__":

    # 1. Clean, one-per-line
    test1 = """
https://youtube.com/watch?v=abc123
https://tiktok.com/@user/video/555
https://instagram.com/reel/xyz
"""
    run_test("One per line", test1)

    # 2. Multiple URLs on the same line
    test2 = "https://youtube.com/abc https://tiktok.com/123 https://instagram.com/reel/xyz"
    run_test("Multiple URLs on one line", test2)

    # 3. URLs separated by commas
    test3 = "https://youtube.com/abc, https://tiktok.com/123,https://instagram.com/reel/xyz"
    run_test("Comma separated", test3)

    # 4. URLs smashed together with no spaces
    test4 = "https://youtu.be/999https://tiktok.com/@user/video/555"
    run_test("Smashed together", test4)

    # 5. Mixed garbage text
    test5 = """
Here are some links I copied:

Check this out https://youtube.com/abc123 it's crazy.
Also this TikTok: https://tiktok.com/@user/video/555
And this IG reel: https://instagram.com/reel/xyz

Random text here, ignore this.
"""
    run_test("Mixed text", test5)

    # 6. No URLs at all
    test6 = "hello world this has no links"
    run_test("No URLs", test6)

