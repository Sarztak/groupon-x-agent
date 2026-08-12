<script>
  import { onMount } from 'svelte'

  const DUMMY_POSTS = [
    { date: 'Mon Jul 27', type: 'deal_drop',  merchant: 'The Spa at LondonHouse Chicago', copy: 'A hotel spa on the Chicago River. Luxury massage, river views, up to 41% off. Find it on Groupon.' },
    { date: 'Tue Jul 28', type: 'deal_drop',  merchant: "Geja's Cafe", copy: "Chicago's fondue institution. $100 dining credit — cheese, chocolate, candlelight. Find it on Groupon." },
    { date: 'Thu Jul 30', type: 'deal_drop',  merchant: 'City Cruises – Seadog Speedboat', copy: 'Lake Michigan at full speed. Chicago skyline behind you. Find it on Groupon.' },
    { date: 'Sat Aug 01', type: 'trend_hook', merchant: '—', trend: '#ChicagoEats', copy: 'Loading...' },
    { date: 'Sun Aug 02', type: 'trend_hook', merchant: '—', trend: '#SelfCareSunday', copy: 'Loading...' },
    { date: 'Tue Aug 04', type: 'deal_drop',  merchant: 'King Spa & Sauna NJ', copy: 'Full-day Korean spa admission — pools, saunas, jjimjilbang. Find it on Groupon.' },
    { date: 'Wed Aug 05', type: 'trend_hook', merchant: '—', trend: '#WellnessWednesday', copy: 'Loading...' },
    { date: 'Thu Aug 06', type: 'deal_drop',  merchant: 'Doodle Yoga SoHo', copy: 'Gentle yoga. Playful goldendoodles. SoHo. Find it on Groupon.' },
    { date: 'Fri Aug 07', type: 'trend_hook', merchant: '—', trend: '#FitnessFriday', copy: 'Loading...' },
    { date: 'Sun Aug 09', type: 'deal_drop',  merchant: 'City Cruises Marina del Rey', copy: 'Premier brunch or dinner cruise on the Marina. LA from the water. Find it on Groupon.' },
  ]

  const DUMMY_THREADS = [
    {
      route: 'deal_request',
      mention: { user: '@sarah_chicago', text: '@Groupon any good spa deals in Chicago this weekend?' },
      reply: 'Generating...',
    },
    {
      route: 'acknowledge',
      mention: { user: '@foodie_nyc', text: '@Groupon the restaurant voucher I bought expired before I could use it and I never got a refund' },
      reply: 'Generating...',
    },
    {
      route: 'positive_response',
      mention: { user: '@marcus_la', text: '@Groupon just got back from the spa deal I booked last week. Best decision I made all month.' },
      reply: 'Generating...',
    },
  ]

  let posts = DUMMY_POSTS
  let threads = DUMMY_THREADS
  let generated = false

  onMount(async () => {
    try {
      const res = await fetch('/api/two_week_plan')
      if (!res.ok) return
      const data = await res.json()
      if (!data.generated) return
      generated = true

      posts = data.posts.map(p => ({
        date:     p.date,
        type:     p.type,
        merchant: p.type === 'trend_hook'
          ? (p.matched_deal?.merchant_name ?? p.trend)
          : p.deal?.merchant_name ?? '',
        trend:    p.trend ?? null,
        copy:     p.copy ?? '—',
        status:   p.status,
      }))

      threads = data.replies.map(r => ({
        route:   r.route ?? r.route_hint,
        mention: { user: '@' + r.username, text: r.text },
        reply:   r.reply ?? '—',
        status:  r.status,
      }))
    } catch (_) {}
  })

  function routeClass(key) {
    const map = {
      deal_drop:        'rc-green',
      trend_hook:       'rc-blue',
      deal_request:     'rc-green',
      acknowledge:      'rc-yellow',
      positive_response:'rc-purple',
    }
    return map[key] ?? 'rc-green'
  }

  $: week1 = posts.slice(0, 5)
  $: week2 = posts.slice(5)
</script>

<div class="content">
  <div class="page-header">
    <div>
      <div class="page-title">Content System</div>
      <div class="page-sub">2-week posting plan · 10 posts across deal drops and trend hooks · 3 sample reply threads · produced by the pipeline</div>
    </div>
    {#if generated}
      <div class="live-badge">Pipeline-generated</div>
    {:else}
      <div class="draft-badge">Draft — dummy data</div>
    {/if}
  </div>

  <!-- POSTING PLAN -->
  <div class="plan-section">
    <div class="section-header">
      <div class="section-title">Posting Schedule</div>
      <div class="legend">
        <span class="leg-item"><span class="leg-dot" style="background:#22c55e"></span>Deal drop</span>
        <span class="leg-item"><span class="leg-dot" style="background:#60a5fa"></span>Trend hook</span>
      </div>
    </div>

    <div class="week-block">
      <div class="week-label">Week 1 · Jul 28 – Aug 2</div>
      <div class="posts-list">
        {#each week1 as post}
          <div class="post-card">
            <div class="post-meta">
              <span class="post-date">{post.date}</span>
              <span class="post-type {routeClass(post.type)}">
                {post.type.replace('_', ' ')}
              </span>
              {#if post.trend}
                <span class="post-trend">↗ {post.trend}</span>
              {/if}
            </div>
            <div class="post-copy">{post.copy}</div>
            <div class="post-merchant">{post.merchant}</div>
          </div>
        {/each}
      </div>
    </div>

    <div class="week-block">
      <div class="week-label">Week 2 · Aug 4 – Aug 10</div>
      <div class="posts-list">
        {#each week2 as post}
          <div class="post-card">
            <div class="post-meta">
              <span class="post-date">{post.date}</span>
              <span class="post-type {routeClass(post.type)}">
                {post.type.replace('_', ' ')}
              </span>
              {#if post.trend}
                <span class="post-trend">↗ {post.trend}</span>
              {/if}
            </div>
            <div class="post-copy">{post.copy}</div>
            <div class="post-merchant">{post.merchant}</div>
          </div>
        {/each}
      </div>
    </div>
  </div>

  <!-- REPLY THREADS -->
  <div class="threads-section">
    <div class="section-title">Sample Reply Threads</div>
    <div class="threads-grid">
      {#each threads as thread}
        <div class="thread-card">
          <div class="route-badge {routeClass(thread.route)}">
            {thread.route.replace(/_/g, ' ')}
          </div>
          <div class="bubble incoming">
            <span class="bubble-user">{thread.mention.user}</span>
            <span class="bubble-text">{thread.mention.text}</span>
          </div>
          <div class="thread-arrow">↓</div>
          <div class="bubble outgoing">
            <span class="bubble-user">@Groupon (agent)</span>
            <span class="bubble-text">{thread.reply}</span>
          </div>
        </div>
      {/each}
    </div>
  </div>

  {#if !generated}
    <div class="disclaimer">Dummy data — run generate_two_week_plan.py to populate with real pipeline outputs</div>
  {/if}
</div>

<style>
  .content {
    flex: 1;
    overflow-y: auto;
    padding: 24px 28px;
    display: flex;
    flex-direction: column;
    gap: 28px;
  }

  .page-header { display: flex; align-items: flex-start; justify-content: space-between; }
  .page-title { font-size: 20px; font-weight: 700; color: var(--c-t1); }
  .page-sub { font-size: 12px; color: var(--c-t2); margin-top: 4px; }

  .live-badge {
    font-size: 11px;
    padding: 4px 12px;
    border-radius: 20px;
    background: var(--c-green-s);
    border: 1px solid var(--c-green-b);
    color: var(--c-green);
    white-space: nowrap;
    flex-shrink: 0;
  }

  .draft-badge {
    font-size: 11px;
    padding: 4px 12px;
    border-radius: 20px;
    background: var(--c-yellow-s);
    border: 1px solid var(--c-yellow-b);
    color: var(--c-yellow);
    white-space: nowrap;
    flex-shrink: 0;
  }

  /* Section headers */
  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
  }

  .section-title {
    font-size: 11px;
    font-weight: 600;
    color: var(--c-t1);
    text-transform: uppercase;
    letter-spacing: 0.07em;
  }

  .legend { display: flex; gap: 14px; }
  .leg-item { display: flex; align-items: center; gap: 5px; font-size: 11px; color: var(--c-t2); }
  .leg-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }

  /* Plan section */
  .plan-section { display: flex; flex-direction: column; gap: 20px; }

  .week-block { display: flex; flex-direction: column; gap: 8px; }

  .week-label {
    font-size: 12px;
    font-weight: 600;
    color: var(--c-t2);
    padding: 0 4px;
  }

  .posts-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 10px;
  }

  .post-card {
    background: var(--c-panel);
    border: 1px solid var(--c-border);
    border-radius: 12px;
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .post-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }

  .post-date {
    font-size: 11px;
    color: var(--c-t2);
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }

  .post-type {
    font-size: 10px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 6px;
    border: 1px solid;
    white-space: nowrap;
  }

  .post-trend {
    font-size: 10px;
    color: var(--c-blue);
    background: var(--c-blue-s);
    border: 1px solid var(--c-blue-b);
    padding: 2px 8px;
    border-radius: 6px;
    white-space: nowrap;
  }

  .post-copy {
    font-size: 13px;
    color: var(--c-t1);
    line-height: 1.55;
  }

  .post-merchant {
    font-size: 10px;
    color: var(--c-t3);
  }

  /* Threads */
  .threads-section { display: flex; flex-direction: column; gap: 12px; }

  .threads-grid {
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .thread-card {
    background: var(--c-panel);
    border: 1px solid var(--c-border);
    border-radius: 12px;
    padding: 14px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .route-badge {
    font-size: 10px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    border: 1px solid;
    align-self: flex-start;
    text-transform: capitalize;
  }

  /* Route color classes (post-type badge + route-badge) */
  .rc-green  { background: var(--c-green-s);  border-color: var(--c-green-b);  color: var(--c-green); }
  .rc-blue   { background: var(--c-blue-s);   border-color: var(--c-blue-b);   color: var(--c-blue); }
  .rc-yellow { background: var(--c-yellow-s); border-color: var(--c-yellow-b); color: var(--c-yellow); }
  .rc-purple { background: var(--c-purple-s); border-color: var(--c-purple-b); color: var(--c-purple); }

  .bubble {
    border-radius: 10px;
    padding: 10px 12px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .bubble.incoming {
    background: var(--c-row);
    border: 1px solid var(--c-border);
  }

  .bubble.outgoing {
    background: var(--c-green-s);
    border: 1px solid var(--c-green-b);
  }

  .bubble-user { font-size: 10px; font-weight: 600; color: var(--c-t2); }
  .bubble.outgoing .bubble-user { color: var(--c-green); }
  .bubble-text { font-size: 12px; color: var(--c-t1); line-height: 1.5; }

  .thread-arrow {
    text-align: center;
    color: var(--c-border);
    font-size: 14px;
  }

  .disclaimer {
    font-size: 11px;
    color: var(--c-t3);
    text-align: center;
    font-style: italic;
    padding-bottom: 8px;
  }
</style>
