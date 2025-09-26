from playwright.sync_api import sync_playwright, expect

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    try:
        # 1. Navigate to the app
        page.goto("http://127.0.0.1:5001")

        # 2. Check for initial bot message
        expect(page.locator(".bot-message")).to_contain_text("Hello! How can I help you today?")

        # 3. Send a message
        page.get_by_placeholder("Type your message...").fill("Hello, bot!")
        page.get_by_role("button", name="Send").click()

        # 4. Wait for and verify user message appears
        expect(page.locator(".user-message")).to_contain_text("Hello, bot!")

        # 5. Wait for and verify bot response appears
        # The bot's response can be variable, so we'll just check that a new bot message exists
        expect(page.locator(".bot-message").nth(1)).to_be_visible(timeout=10000)

        # 6. Take a screenshot
        page.screenshot(path="jules-scratch/verification/verification.png")

        print("Verification script ran successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
        page.screenshot(path="jules-scratch/verification/error.png")

    finally:
        browser.close()

with sync_playwright() as playwright:
    run(playwright)