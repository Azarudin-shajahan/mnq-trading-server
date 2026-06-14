# AdiiX — "AUTOMATIC TRADING WITH CLAUDE FABLE FULL GUIDE" (transcript + notes)

- **Source**: https://x.com/adiix_official/status/2065023269103714770
- **Length**: 13:00 (1080p)
- **Captured**: 2026-06-13 — downloaded via yt-dlp, transcribed locally (whisper-cpp base model)
- **Type**: competitive intel / not a research input. Trading project research stays CLOSED.

## Method (real build steps, hype stripped)
Three escalating tests of Claude Code/Desktop ("Fable 5") as a trading agent:
1. **No-tools control**: standard prompt with rules (BTCUSDT 1h; no extra tools; no multi-TF / multi-TP = repaint guard). Claude writes a Pine strategy (FastMA/SlowMA + ADX + SMA + RSI) -> TradingView. ~PF 1.08-1.12, 31% WR, 19.6% DD.
2. **trader.dev backtest MCP** (his own free tool): install = site -> Account -> copy one line -> paste to Claude -> "install it". Then prompt to optimize/sweep every ~5 min, look beyond crypto, and LOOP for hours (self-search settings). BTCUSDT 4h: PF 1.71 / +112% / -27.5% DD / 65 trades / 43% WR.
3. **Strategy Factory skill** into Claude Desktop: connects to exchange (Bybit), can place real orders (market/SL/TP, DCA bot, grid bot, "move stop to BE in profit"). API keys encrypted locally. Live prompt: "update your skills, learn from past mistakes, find me 3 trades, all market orders." Claude placed 3 longs on 10x isolated leverage (SUI/DOGE/SAHARA), then unprompted monitored + closed them and rewrote its own skill files. Net -$20.

## Honest caveats shown on screen
- Headline +112% carries -27.5% max drawdown; other equity curves (Apple, TJX +2520%) ride 50%+ drawdowns.
- His own trader.dev report: OOS PF degraded 2.83 -> 1.26 (train 2021-23, validate 2024-26); 9 improvement candidates rejected on a robustness gate.
- Build steps are trivial (2 copy-paste installs + a rules prompt + loop); numbers are standard in-sample optimism.

## Relevance to this project
Same architecture we already have (mnq-server execution relay, backtest harness, Fable analyst, kill-criteria gate). The two pieces AdiiX wires that we don't: a looping self-optimization cycle + agent-driven live order placement.

---

## Full timestamped transcript

[00:00:00] USDT.
[00:00:01] Number two, we're going to be giving it the tools so it can actually backtest those strategies.
[00:00:06] Yes, I have built an MCP server that allows Claude to be able to backtest strategies.
[00:00:12] We're going to put it in a loop and ask it to use self-learning techniques to build
[00:00:16] something that is much more profitable and robust over time.
[00:00:20] And finally, the third test is going to be asking Claude to take a trade.
[00:00:25] That might sound something easy, but we're actually going to give it tools, build its own
[00:00:29] scalping strategy on a low time frame allowing it to take multiple trades over a 1 hour period
[00:00:35] to see whether or not it can actually make some profit.
[00:00:38] So if that sounds good to you, let's move on, let's get back over to the screen
[00:00:42] and let's push those limits of Claude 5.
[00:00:44] I'm now integrating AI into my daily processes here,
[00:00:48] transparently on my channel, trying to make my strategies even more profitable
[00:00:52] and more automated thanks to AI.
[00:00:54] And guys, don't forget if you want access to all of my prompts,
[00:00:57] the tools that I used are all 100% for free.
[00:01:01] Comment, Claude, Fable 5 in the comment section down below.
[00:01:05] And I will get my workbook to as fast as I possibly can.
[00:01:08] Okay, so let's get over to my computer, let's have a look at the most recent update of Claude
[00:01:14] and see whether or not we can actually make something more profitable.
[00:01:17] Okay, so here are the benchmarks that everybody's talking about on Twitter.
[00:01:21] As you can see, we have our most recent version here of Fable 5, which was released a couple of hours ago
[00:01:30] and just glancing over it, you can see that the improvements were absolutely exponential.
[00:01:36] Agentic coding has gone from 69.2% to 80%.
[00:01:41] Agentic coding benchmarked, we're up over double.
[00:01:44] So we're in from 13.4% up to 29.3%.
[00:01:48] Knowledge work up every single benchmark has been absolutely crushed,
[00:01:54] including all of the benchmarks which I use a lot more would be the coding ones here.
[00:01:59] Cybersecurity is up almost double on what it previously was.
[00:02:04] So I'm very, very excited about testing this model to see what we can actually push out of it.
[00:02:10] So we have this model here, but we are missing a couple of columns on the side here.
[00:02:15] We don't know whether it can actually make a profitable trading strategy
[00:02:18] and can it actually make profitable trades on an exchange.
[00:02:21] So I'm going to be testing all of that directly on Claude code.
[00:02:25] Okay, so here we are back on a new session.
[00:02:28] I'm going to switch the model across over to five.
[00:02:32] And let's give a Claude our prompt.
[00:02:34] Now, for every one of these tests, I have given a standard prompt.
[00:02:38] In that prompt, I've given a couple of rules, including that it's not allowed to use any extra tools.
[00:02:44] They must come up with something that is profitable on BTCUSDT,
[00:02:49] on the one hour time frame.
[00:02:52] It mustn't use things like multiple take profits on multiple time frames
[00:02:56] because that may create what we call repainting, which pretty much is cheating.
[00:03:01] Guys, as I said earlier, if you want access to my workbooks,
[00:03:04] all of the prompts and the tools that I use for free,
[00:03:08] don't forget to come in Claude 5 down in the description down below.
[00:03:11] So all of the rules are in place. We're going to have work that into a button
[00:03:15] and leave Claude to go away and actually code that strategy.
[00:03:19] Okay, we're starting to get some logic after three minutes of waiting.
[00:03:25] One thing I noticed is that it isn't the fastest model in the world,
[00:03:28] but the actual servers may be overrun at the moment.
[00:03:32] As you can see, it's going through all of its logic.
[00:03:34] First of all, it's come up with something which is great.
[00:03:37] Most trend followers don't predict that they position the edge comes from
[00:03:41] four principles, trade only when the regime actually exists, asymmetric pay off,
[00:03:47] confirmation stacking and survival first.
[00:03:51] Now that is absolutely insane, brilliant, brilliant advice,
[00:03:55] and couldn't have said it better myself.
[00:03:57] But then you look at some of the indicators that it's using,
[00:03:59] it's using the FastDMA, the SlowDMA, ADX,
[00:04:03] another SMA, RSI.
[00:04:05] I guess, yeah, is what it is.
[00:04:07] Let's see whether or not this actually is a good strategy.
[00:04:10] Let's have a look at the code very quickly.
[00:04:12] I won't go into deep detail.
[00:04:13] We can see the indicators just there.
[00:04:15] The risk management looks good.
[00:04:17] And hopefully we've finished.
[00:04:19] Okay, let's go and copy this over to TradingView
[00:04:22] to see whether or not it's actually profitable.
[00:04:24] Boom, let's go.
[00:04:26] Okay, now this is the first in a long, long while.
[00:04:30] We saved it, and it actually doesn't have any errors.
[00:04:34] And we edit to our charts.
[00:04:36] And it's not the ugliest equity curve ever.
[00:04:40] I've got to say, for an AI without any tools,
[00:04:43] this isn't bad at all.
[00:04:45] Let's have a look at some other timeframes.
[00:04:47] Two hours, it's profitable, went through some huge drawdown.
[00:04:50] But it is 13% up.
[00:04:53] Let's have a look on full history.
[00:04:56] And full history, we actually do have something that's pretty profitable.
[00:04:59] Let's go back to the one hour timeframe
[00:05:01] and look on full history.
[00:05:03] And again, a profitable strategy, not a nice strategy,
[00:05:07] but a profitable strategy.
[00:05:09] We have an entire history.
[00:05:10] Let's go over two four hours.
[00:05:12] And again, now that is starting to look much, much cleaner
[00:05:16] as an equity curve.
[00:05:17] We have a 31% win rate, 12% makes drawdown.
[00:05:21] And we have a PLL of 21%.
[00:05:24] Probably a factor is 1.12.
[00:05:25] So that's positive for this strategy.
[00:05:28] Finally, let's go and have a look at a low time frame to see.
[00:05:31] When or not, this is any good on lower timeframes.
[00:05:33] And on low timeframes, it doesn't look good at all.
[00:05:35] Let's have a look very quickly.
[00:05:36] Either or not we've actually added, it has added commission.
[00:05:40] Quantity, one slippage, it has added slippage.
[00:05:43] So yeah, we certainly couldn't ask for more out of a trading strategy.
[00:05:47] Absolutely brilliant.
[00:05:48] Yeah, we've got to give Claude a round of applause for that.
[00:05:51] Okay, so pretty impressed.
[00:05:53] As I said earlier, let's move on.
[00:05:54] Let's give Claude the tools so it can actually backtest
[00:05:58] and create something a little bit more special.
[00:06:00] Okay, so test two, we're going to be giving Claude
[00:06:02] the actual tools so it can actually backtest the strategies.
[00:06:06] We go over to trader.dev.
[00:06:08] This is a free tool that I made which allows us
[00:06:11] to backtest trading strategies.
[00:06:13] We've built over 63,000 backtest of strategies
[00:06:18] as a huge quantity of people working together
[00:06:21] to find the best settings.
[00:06:22] It's very, very simple to install.
[00:06:24] You just click over here on account.
[00:06:26] Click on account and then you copy this line of code.
[00:06:30] Give it to Claude, ask it to install it.
[00:06:32] And then you have the power of a backtest
[00:06:35] that it works on crypto.
[00:06:36] It works on gold, silver, forex, whatever you want.
[00:06:39] You can actually backtest those strategies.
[00:06:41] So I'm going to go over here.
[00:06:43] We've already created a simple, back-powerful prompt
[00:06:47] that asks it to go through and optimize every five minutes
[00:06:50] to do try and find the best settings.
[00:06:53] We're going to work on the intat.
[00:06:55] I'm going to go through the prompt very, very quickly with you.
[00:06:57] It is very much similar to the other one just there
[00:06:59] except for we're giving access to trader.dev's tools
[00:07:02] so it can start actually backtesting the strategies.
[00:07:05] So this is going to go away and think about it.
[00:07:06] Now I'm going to leave that for a couple of hours
[00:07:08] to try and find the best settings.
[00:07:10] I've also asked it not to only look at crypto
[00:07:12] and maybe look outside of the crypto world
[00:07:15] and try and find some best settings for trading view.
[00:07:18] Let's move on to test the three.
[00:07:20] Whilst that's actually doing those backtests,
[00:07:22] let's find out whether or not Fable 5 can actually build
[00:07:25] its own live trading system, take trades on a buy-a-bit
[00:07:29] and actually make us some money.
[00:07:31] So I'm going to go back over to here
[00:07:33] which is my buy-a-bit live session.
[00:07:35] We've already set Fable 5 at just here
[00:07:37] and I'm going to be using this tool just here.
[00:07:40] Okay, so this is my strategy factory skill.
[00:07:43] What this allows Claude to do is actually connect over to your exchange.
[00:07:48] What this actually does is it gives it Claude
[00:07:50] the power to connect over to your exchange
[00:07:52] but not only that it allows it to take trades for you.
[00:07:55] You can set up things like a DCA bot,
[00:07:58] a grid bot, use the DavidTicket strategies
[00:08:01] or even just take trades.
[00:08:03] It's great for risk management
[00:08:05] because you can say hey there Claude could you please
[00:08:08] move my stop blaster to break even as soon as we get into profit
[00:08:12] and things like that by just naturally talking to Claude
[00:08:15] which can actually save you money and time
[00:08:17] because you're not actually having to stare at charts all day long.
[00:08:20] Right, okay, so what we're going to do here
[00:08:22] is we're just going to copy this
[00:08:23] and paste it over into our Claude desktop.
[00:08:27] We will ask it to install it
[00:08:29] and I've already installed it so I'm not going to do it again.
[00:08:32] It will take you through the onboarding process
[00:08:34] where it asks you to add your API's
[00:08:37] fuel exchange
[00:08:38] and which are encrypted on your computer
[00:08:40] not in the slightest in the cloud anywhere
[00:08:42] they're just on your computer
[00:08:44] so you don't have to worry about mass hacks
[00:08:45] or anything like that.
[00:08:46] Okay, so on the left side
[00:08:49] we have our Claude with our skills installed
[00:08:52] on the right side we have my bi-bit account.
[00:08:55] Let's ask Claude Claude with your skills in this folder.
[00:08:59] I'd love for you to update those skills
[00:09:02] with all of your new knowledge.
[00:09:04] You are the most powerful model out there.
[00:09:07] You understand markets like nobody else.
[00:09:10] These school skills update them
[00:09:12] learn from your previous mistakes
[00:09:14] and find me three trades.
[00:09:17] I want the stop loss to take profit
[00:09:19] and the actual entry all market orders
[00:09:22] by me three trades which we can potentially take right now.
[00:09:26] Boom, it's going to use the skills that it's actually built
[00:09:29] it's going to update them
[00:09:30] it's going to find make them better and more powerful
[00:09:32] hopefully we'll get three trades.
[00:09:34] Okay, this is the first that's ever happened
[00:09:38] it didn't even ask me how much I wanted to take
[00:09:41] it's probably from previous chats
[00:09:42] it's actually taken three trades
[00:09:44] for me three longer trades
[00:09:47] on isolated 10X leverage
[00:09:50] I don't think I actually put it in there
[00:09:51] now that's what you call taking control
[00:09:54] yeah that's the first time it happens to me
[00:09:56] it's taken three actual trades
[00:09:58] for me sui USDT long dojo's USDT
[00:10:02] and Sahara USDT
[00:10:05] let's have a look at our P&L
[00:10:07] we're going to be in profit on one down
[00:10:09] by a 1% on the two other trades
[00:10:12] right okay these are all going to sit
[00:10:14] in the background for a couple of hours
[00:10:16] for up to two hours
[00:10:17] I'm going to see whether or not we're actually profitable
[00:10:20] and we're going to see whether or not
[00:10:21] he can actually make a profitable trading strategies
[00:10:23] I'll be back in a couple of seconds
[00:10:25] okay we're back and yeah um so we've got some
[00:10:29] interesting results here
[00:10:31] let's start off with the trading with
[00:10:33] buy bit all three positions are closed
[00:10:36] and as you can see from the actual results
[00:10:39] Fible 5 actually took it into its own hands
[00:10:43] to close to trades manually
[00:10:46] and let one hit the actual stop loss
[00:10:49] unfortunately that means the we're USD$20
[00:10:51] down but on the flip side
[00:10:54] this thing just decided to work for itself
[00:10:57] I mean no way did I ask it to do this
[00:11:00] it was just monitoring the market
[00:11:02] I left it running
[00:11:03] I saw that the task was still running
[00:11:06] it started to monitor its own trades
[00:11:09] you can see that it checked
[00:11:11] every 15-20 minutes of the stop loss
[00:11:15] and it closed all of the trades
[00:11:17] whether they're profitable or not
[00:11:19] it is something absolutely insane
[00:11:22] in one of the notes I also noticed
[00:11:24] that it started updating its own skills
[00:11:27] as a kind of a self-learning process
[00:11:30] which I've got to say actually blows my socks off
[00:11:33] so anyway next we're going to be going over
[00:11:35] to the backtesting results
[00:11:37] and as you can see the backtesting results are
[00:11:39] pretty much the same thing
[00:11:41] it started to build on BTC
[00:11:43] and then decided that BTC wasn't the only way forward
[00:11:46] it started looking at other timeframes
[00:11:48] adding multiple pairs
[00:11:50] and coming up with its own strategies
[00:11:52] I also ran in parallel a second one
[00:11:55] because I couldn't get the first one actually
[00:11:57] to run by itself
[00:11:58] and the results were even better
[00:12:01] I mean we're up at 119%
[00:12:03] and 1.78 profit factor
[00:12:07] furthered we get down the list
[00:12:08] the better the results seem to actually get
[00:12:11] it is pretty insane
[00:12:12] let's have a look at some of the equity curves
[00:12:14] that you come up with the equity curve
[00:12:16] isn't perfect
[00:12:17] this has only been going for one hour
[00:12:19] and it's profitable 112% profit
[00:12:22] the equity curve isn't great here
[00:12:24] but it still is profitable
[00:12:26] on Ethereum another four hour strategy
[00:12:28] looking pretty insane
[00:12:30] so that's just one hour's work
[00:12:32] but I have something else to show you
[00:12:34] here is a strategy on Apple
[00:12:35] here on the Nasdaq Apple one day chart
[00:12:38] look at the equity curve on that
[00:12:40] I have another one here
[00:12:42] which is TJX companies
[00:12:45] and this one is on the four hour time frame
[00:12:48] look at this equity curve
[00:12:50] and these are kind of strategies
[00:12:51] that have actually been built
[00:12:53] by this new model within a couple of hours
[00:12:56] of just literally backtesting
[00:12:58] and self-improving
