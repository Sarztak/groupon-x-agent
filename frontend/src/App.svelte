<script>
  import Controls from './components/Controls.svelte'
  import ChatView from './components/ChatView.svelte'
  import ReviewView from './components/ReviewView.svelte'

  let mode = 'deal_drop'
  let segment = 'spontaneous_locals'
  let variations = 1

  let messages = []
  let reviewItems = []
  let nextId = 0

  function addMessage(text, direction, meta = null) {
    messages = [...messages, { type: 'message', text, direction, meta, id: nextId++ }]
  }

  function addPill(text, variant) {
    messages = [...messages, { type: 'pill', text, variant, id: nextId++ }]
  }

  function delay(ms) {
    return new Promise(r => setTimeout(r, ms))
  }

  async function handleRun() {
    if (mode === 'deal_drop') {
      addPill('Deal drop triggered', 'routing')
      await delay(1000)
      addPill('Review passed', 'pass')
      addMessage(
        'Pittsburgh, your shoulders called. Honor Your Body Wellness has been waiting. Up to 52% off personalized therapeutic massages — deep tissue, Swedish, or couples. Book on Groupon.',
        'outgoing', 'Agent · deal drop'
      )
    }

    else if (mode === 'trend_hook') {
      addMessage('#SelfCareSunday is trending · 85,000 tweets', 'incoming', 'Trend signal')
      await delay(900)
      addPill('Matched: King Spa Chicago', 'routing')
      await delay(900)
      addPill('Review passed', 'pass')
      addMessage(
        "It's Sunday. King Spa Chicago has heated pools, sauna rooms, and a plunge. Open 24/7. All-day admission on Groupon.",
        'outgoing', 'Agent · trend hook'
      )
    }

    else if (mode === 'mention_reply') {
      addMessage('@Groupon any good spa deals in Chicago this weekend?', 'incoming', '@sarah_chicago')
      await delay(700)
      addPill('Guard passed', 'pass')
      await delay(800)
      addPill('Review passed', 'pass')
      addMessage(
        '@sarah_chicago King Spa Chicago — heated pools, sauna rooms, scrubs. All day, any time. On Groupon right now.',
        'outgoing', 'Agent · mention reply'
      )
    }
  }

  async function handleSend(text) {
    const negativePattern = /sucks|terrible|awful|hate|scam|worst|refund|complaint|issue|broken|fraud|ripoff/i

    if (mode === 'mention_reply') {
      addMessage(text, 'incoming', 'Custom mention')
      await delay(600)

      if (negativePattern.test(text)) {
        addPill('Guard: escalating to human', 'escalate')
        reviewItems = [...reviewItems, {
          id: nextId++,
          input: text,
          reason: 'Negative sentiment or complaint detected — requires human response',
          suggestion: "We hear you. Please DM us your order details and we'll make this right."
        }]
      } else {
        addPill('Guard passed', 'pass')
        await delay(800)
        addPill('Review passed', 'pass')
        addMessage(
          'Check out our latest local deals on Groupon — something good is near you.',
          'outgoing', 'Agent · mention reply'
        )
      }
    }

    else if (mode === 'trend_hook') {
      addMessage(text + ' is trending', 'incoming', 'Custom trend')
      await delay(600)
      addPill('Matching deal...', 'routing')
      await delay(900)
      addPill('Review passed', 'pass')
      addMessage(
        'Something worth leaving the house for is happening in your city. Find it on Groupon.',
        'outgoing', 'Agent · trend hook'
      )
    }
  }

  function handleApprove(item) {
    addMessage(item.suggestion, 'outgoing', 'Human approved · sent')
    reviewItems = reviewItems.filter(r => r.id !== item.id)
  }

  function handleDiscard(item) {
    reviewItems = reviewItems.filter(r => r.id !== item.id)
  }
</script>

<div class="app">
  <Controls
    bind:mode
    bind:segment
    bind:variations
    onRun={handleRun}
  />

  <div class="body">
    <ChatView
      {messages}
      {mode}
      onSend={handleSend}
    />

    <ReviewView
      items={reviewItems}
      onApprove={handleApprove}
      onDiscard={handleDiscard}
    />
  </div>
</div>

<style>
  :global(*, *::before, *::after) { box-sizing: border-box; margin: 0; padding: 0; }

  :global(body) {
    background: #000000;
    color: #e7e9ea;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    height: 100vh;
    overflow: hidden;
  }

  :global(#app) {
    height: 100vh;
    display: flex;
    flex-direction: column;
  }

  .app {
    display: flex;
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
  }

  .body {
    display: flex;
    flex: 1;
    overflow: hidden;
  }
</style>
