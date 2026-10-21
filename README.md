# Daily Market Digest Bot (free GitHub Actions version)

PDF digest to your Telegram around 7:30 AM IST every day. Your questions and commands are answered on the next check (about every 10 minutes). No server needed.

## Setup
1. **Secrets:** repo > Settings > Secrets and variables > Actions > New repository secret. Add:
   - `TELEGRAM_BOT_TOKEN` (from @BotFather > /mybots > your bot > API Token)
   - `ANTHROPIC_API_KEY` (console.anthropic.com; needs a small prepaid balance)
   - `OWNER_CHAT_ID` (see step 3)
2. Open your bot in Telegram and send `/start`. Wait up to 10 minutes: it replies with your chat ID. (Run the "Check chat" workflow manually from the Actions tab to speed this up.)
3. Add that number as the `OWNER_CHAT_ID` secret. From now on only you get answers.
4. Test: Actions tab > "Daily digest" > Run workflow. The PDF should arrive in Telegram.

## Good to know
- GitHub may start scheduled jobs 5-20 minutes late, so "7:30" can slip a little.
- GitHub pauses scheduled workflows in a public repo after 60 days with no repo activity. If the bot goes quiet, open the Actions tab and re-enable it (or make any small commit).
- Each digest or answer uses Anthropic API credits.
- Edit `sources.py` to change channels. Informational only, not investment advice.
