### Top.gg Webhook Vote Poster

This project is a standalone Top.gg webhook vote poster and is not a part of your bot's main codebase. If your bot is listed on Top.gg and you wish to use a webhook for tracking and displaying votes, this folder provides an easy-to-deploy solution.

# You can remove this top-gg folder if you don't plan to use the Top.gg webhook functionality.

What Does This Do?

This script listens for vote events from Top.gg and posts a customized webhook message (including user vote stats) to your Discord server or desired endpoint. It works independently and can be deployed on any free hosting platform.


---

How to Use

1. Set Up Top.gg Webhook:

Go to your bot's Top.gg dashboard.

Enable the webhook and set the webhook URL to the one provided after deployment.



2. Deploy the Folder:

Use any free hosting platform like Render, Railway, Vercel, or Fly.io.

Deploy the folder and note the generated URL.



3. Configure Your Environment:

Add your bot token, webhook authorization key, and other required details in the environment variables of the hosting platform.



4. Testing:

Use the POST method on the deployed URL to ensure it responds correctly with the right authorization.





---

Free Deployment Platforms

Here are some platforms you can use for deployment:

• Render
• Railway
• Vercel
• Fly.io

I'm using Render so i would recommend to use render to deploy for free.


---

Key Features

Tracks and posts detailed user stats like total votes, streaks, and next vote timestamps.

Integrates seamlessly with Top.gg's webhook API.

Lightweight and independent from your main bot's code.



---

Why Keep This Separate?

This webhook script is standalone to reduce dependencies and ensure your bot’s main functionality remains unaffected. Deploying it separately gives you:

Flexibility: Use any deployment service.

Reliability: Isolate the webhook logic from the bot's code.

Ease of Management: Updates to this webhook script won’t impact your bot.


