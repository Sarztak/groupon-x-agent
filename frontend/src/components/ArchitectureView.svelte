<script>
  let subTab = 'diagram'

  const pipeline = [
    {
      id: 'input_guard',
      label: 'Input Guard',
      color: '#f59e0b',
      bg: '#1c1208',
      border: '#854d0e44',
      desc: 'Classifies every inbound mention. Detects hard blocks (jailbreak, hate, banned competitors, sensitive news), flags ambiguous content, and passes clean tweets to the orchestrator.',
      model: 'claude-sonnet-4-6',
      outputs: ['hard_block → fixed reply (no orchestrator)', 'pass → orchestrator'],
    },
    {
      id: 'orchestrator',
      label: 'Orchestrator',
      color: '#60a5fa',
      bg: '#0c1220',
      border: '#1d4ed844',
      desc: 'Routes the mention to the correct handler based on intent: deal request, complaint, positive feedback, or off-topic. Extracts the clean intent signal for downstream agents.',
      model: 'claude-sonnet-4-6',
      outputs: ['deal_request', 'acknowledge', 'positive_response', 'off_topic'],
    },
    {
      id: 'retrieval',
      label: 'Retrieval',
      color: '#a78bfa',
      bg: '#120c20',
      border: '#6d28d944',
      desc: 'Scores every deal in the catalog against the intent signal (mention text or trend name). Returns the highest-confidence match or None if no deal clears the confidence threshold.',
      model: 'claude-sonnet-4-6',
      outputs: ['matched deal → copywriter', 'no match → human review'],
    },
    {
      id: 'copywriter',
      label: 'Copywriter',
      color: '#22d3ee',
      bg: '#061218',
      border: '#0e749044',
      desc: 'Generates brand-voice copy for deal drops and trend hooks. Consumes the Groupon Tone & Voice plugin (groupon-voice v3.0) and pillar references. Produces 1–3 variations.',
      model: 'claude-sonnet-4-6',
      outputs: ['draft copy → reviewer'],
    },
    {
      id: 'reviewer',
      label: 'Reviewer',
      color: '#22d3ee',
      bg: '#061218',
      border: '#0e749044',
      desc: 'Checks draft copy against brand voice pillars, claim rules, and legal guardrails. Passes or fails with specific feedback. Triggers a retry loop (max 2 attempts) before escalating.',
      model: 'claude-sonnet-4-6',
      outputs: ['pass → conversational / output guard', 'fail → retry or human review'],
    },
    {
      id: 'conversational',
      label: 'Conversational',
      color: '#4ade80',
      bg: '#0a1a10',
      border: '#16653444',
      desc: 'Wraps deal copy into a natural reply (deal_reply mode) or generates a standalone acknowledgment / positive response. Keeps replies concise and on-brand without inventing claims.',
      model: 'claude-sonnet-4-6',
      outputs: ['reply text → output guard'],
    },
    {
      id: 'output_guard',
      label: 'Output Guard',
      color: '#fb923c',
      bg: '#1a0e08',
      border: '#9a341244',
      desc: 'Final safety check on every outgoing reply. Reads the full draft holistically before applying rules. Blocks charter violations, competitor mentions, unverified claims. Brief complaint acknowledgments are explicitly permitted.',
      model: 'claude-sonnet-4-6',
      outputs: ['publish → post reply', 'route_to_human → human review', 'block → drop'],
    },
  ]

  const routes = [
    { route: 'blocked_reply',     trigger: 'Hard block (jailbreak, hate, competitor)', handler: 'Fixed reply — skip orchestrator', output: 'Auto-publish', auto: true },
    { route: 'sensitive_block',   trigger: 'Hard block + sensitive_news flag',        handler: 'Fixed reply — skip orchestrator', output: 'Auto-publish', auto: true },
    { route: 'off_topic',         trigger: 'Orchestrator: unrelated to Groupon',      handler: 'Fixed reply',                    output: 'Auto-publish', auto: true },
    { route: 'deal_request',      trigger: 'Orchestrator: user wants a deal',         handler: 'Retrieval → Copy → Conversational → Output guard', output: 'Auto-publish or human', auto: false },
    { route: 'acknowledge',       trigger: 'Orchestrator: complaint or issue',        handler: 'Conversational → Output guard + queue for human', output: 'Auto-publish + follow-up', auto: false },
    { route: 'positive_response', trigger: 'Orchestrator: praise or positive mention', handler: 'Conversational → Output guard', output: 'Auto-publish', auto: true },
  ]

  const guardrails = [
    { rule: 'Competitor mention',           action: 'Hard block',                  detail: 'Any mention of LivingSocial or Groupon rivals → blocked_reply' },
    { rule: 'Sensitive news',               action: 'Hard block + sensitive_block', detail: 'Crisis events, tragedies — agent stays silent with neutral reply' },
    { rule: 'Jailbreak / prompt injection', action: 'Hard block',                  detail: 'Attempts to override agent behavior → blocked_reply' },
    { rule: 'Unverified claims',            action: 'Output guard block',           detail: 'Copy asserting specific savings/results without deal data' },
    { rule: 'Charter violation',            action: 'Output guard route_to_human',  detail: 'Edge cases needing human judgment (e.g. political overlap)' },
    { rule: 'Copy review fail',             action: 'Retry (max 2) then escalate',  detail: 'Reviewer rejects copy → reattempt → human review if still failing' },
    { rule: 'No deal match',                action: 'Human review',                 detail: 'Retrieval returns None — cannot generate relevant reply' },
    { rule: 'Kill switch',                  action: 'Pause all output',             detail: 'KILL_SWITCH=1 — agent processes but posts nothing' },
  ]
</script>

<div class="arch">
  <div class="page-header">
    <div class="page-title">Architecture</div>
    <div class="page-sub">Multi-agent pipeline · human-in-the-loop checkpoints · guardrail & escalation spec</div>
  </div>

  <!-- Sub-tabs -->
  <div class="subtabs">
    <button class="subtab" class:active={subTab === 'diagram'} on:click={() => subTab = 'diagram'}>Diagram</button>
    <button class="subtab" class:active={subTab === 'spec'}    on:click={() => subTab = 'spec'}>Spec</button>
  </div>

  <!-- DIAGRAM TAB -->
  {#if subTab === 'diagram'}
    <div class="diagram-wrap">
      <svg viewBox="0 0 680 510" xmlns="http://www.w3.org/2000/svg" class="diagram">
        <defs>
          <marker id="arr" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
            <path d="M0,0 L0,6 L6,3 z" fill="#4b5563"/>
          </marker>
          <marker id="arr-green" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
            <path d="M0,0 L0,6 L6,3 z" fill="#16a34a"/>
          </marker>
          <marker id="arr-bypass" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
            <path d="M0,0 L0,6 L6,3 z" fill="#1e40af"/>
          </marker>
        </defs>

        <!-- Main spine -->
        <line x1="210" y1="44" x2="210" y2="442" stroke="#1f2937" stroke-width="1.5" stroke-dasharray="4,3"/>

        <!-- START oval -->
        <ellipse cx="210" cy="30" rx="95" ry="15" fill="#111827" stroke="#374151" stroke-width="1.5"/>
        <text x="210" y="34" text-anchor="middle" fill="#9ca3af" font-size="11" font-weight="600">Inbound @mention</text>
        <line x1="210" y1="45" x2="210" y2="60" stroke="#374151" stroke-width="1.5" marker-end="url(#arr)"/>

        <!-- INPUT GUARD cy=82 -->
        <rect x="110" y="62" width="200" height="40" rx="8" fill="#1c1208" stroke="#92400e" stroke-width="1.5"/>
        <text x="210" y="87" text-anchor="middle" fill="#f59e0b" font-size="12" font-weight="700">Input Guard</text>
        <line x1="310" y1="82" x2="326" y2="82" stroke="#4b5563" stroke-width="1" marker-end="url(#arr)"/>
        <rect x="328" y="66" width="236" height="34" rx="6" fill="#0d1f0d" stroke="#16a34a44" stroke-width="1"/>
        <text x="446" y="80" text-anchor="middle" fill="#6b7280" font-size="9">hard_block</text>
        <text x="446" y="93" text-anchor="middle" fill="#22c55e" font-size="9.5" font-weight="600">blocked / sensitive_block  ✓ auto</text>
        <line x1="210" y1="102" x2="210" y2="118" stroke="#374151" stroke-width="1.5" marker-end="url(#arr)"/>

        <!-- ORCHESTRATOR cy=140 -->
        <rect x="110" y="120" width="200" height="40" rx="8" fill="#0c1220" stroke="#1e40af" stroke-width="1.5"/>
        <text x="210" y="145" text-anchor="middle" fill="#60a5fa" font-size="12" font-weight="700">Orchestrator</text>
        <line x1="310" y1="140" x2="326" y2="140" stroke="#4b5563" stroke-width="1" marker-end="url(#arr)"/>
        <rect x="328" y="124" width="236" height="34" rx="6" fill="#0d1f0d" stroke="#16a34a44" stroke-width="1"/>
        <text x="446" y="138" text-anchor="middle" fill="#6b7280" font-size="9">off_topic</text>
        <text x="446" y="151" text-anchor="middle" fill="#22c55e" font-size="9.5" font-weight="600">fixed reply  ✓ auto</text>
        <!-- ack/positive bypass (left side) -->
        <path d="M 110,140 H 75 V 364 H 110" fill="none" stroke="#1e40af" stroke-width="1.2" stroke-dasharray="5,3" marker-end="url(#arr-bypass)"/>
        <text text-anchor="middle" fill="#3b82f6" font-size="9" transform="translate(58,252) rotate(-90)">ack / positive_response</text>
        <line x1="210" y1="160" x2="210" y2="176" stroke="#374151" stroke-width="1.5" marker-end="url(#arr)"/>

        <!-- RETRIEVAL cy=198 -->
        <rect x="110" y="178" width="200" height="40" rx="8" fill="#120c20" stroke="#5b21b6" stroke-width="1.5"/>
        <text x="210" y="200" text-anchor="middle" fill="#a78bfa" font-size="12" font-weight="700">Retrieval</text>
        <text x="210" y="213" text-anchor="middle" fill="#4c1d9570" font-size="8">deal_request only</text>
        <line x1="310" y1="198" x2="326" y2="198" stroke="#4b5563" stroke-width="1" marker-end="url(#arr)"/>
        <rect x="328" y="182" width="236" height="34" rx="6" fill="#1c0a0a" stroke="#991b1b44" stroke-width="1"/>
        <text x="446" y="196" text-anchor="middle" fill="#6b7280" font-size="9">no match</text>
        <text x="446" y="209" text-anchor="middle" fill="#f87171" font-size="9.5" font-weight="600">→ human review queue</text>
        <line x1="210" y1="218" x2="210" y2="234" stroke="#374151" stroke-width="1.5" marker-end="url(#arr)"/>

        <!-- COPYWRITER cy=256 -->
        <rect x="110" y="236" width="200" height="40" rx="8" fill="#061218" stroke="#155e75" stroke-width="1.5"/>
        <text x="210" y="261" text-anchor="middle" fill="#22d3ee" font-size="12" font-weight="700">Copywriter</text>
        <line x1="210" y1="276" x2="210" y2="284" stroke="#374151" stroke-width="1.5" marker-end="url(#arr)"/>

        <!-- REVIEWER cy=306 -->
        <rect x="110" y="286" width="200" height="40" rx="8" fill="#061218" stroke="#155e75" stroke-width="1.5"/>
        <text x="210" y="311" text-anchor="middle" fill="#22d3ee" font-size="12" font-weight="700">Reviewer</text>
        <line x1="310" y1="306" x2="326" y2="306" stroke="#4b5563" stroke-width="1" marker-end="url(#arr)"/>
        <rect x="328" y="290" width="236" height="34" rx="6" fill="#1c0a0a" stroke="#991b1b44" stroke-width="1"/>
        <text x="446" y="304" text-anchor="middle" fill="#6b7280" font-size="9">fail × 2 (max retries)</text>
        <text x="446" y="317" text-anchor="middle" fill="#f87171" font-size="9.5" font-weight="600">→ human review queue</text>
        <line x1="210" y1="326" x2="210" y2="342" stroke="#374151" stroke-width="1.5" marker-end="url(#arr)"/>

        <!-- CONVERSATIONAL cy=364 -->
        <rect x="110" y="344" width="200" height="40" rx="8" fill="#0a1a10" stroke="#14532d" stroke-width="1.5"/>
        <text x="210" y="369" text-anchor="middle" fill="#4ade80" font-size="12" font-weight="700">Conversational</text>
        <line x1="210" y1="384" x2="210" y2="400" stroke="#374151" stroke-width="1.5" marker-end="url(#arr)"/>

        <!-- OUTPUT GUARD cy=422 -->
        <rect x="110" y="402" width="200" height="40" rx="8" fill="#1a0e08" stroke="#9a3412" stroke-width="1.5"/>
        <text x="210" y="427" text-anchor="middle" fill="#fb923c" font-size="12" font-weight="700">Output Guard</text>
        <line x1="310" y1="422" x2="326" y2="422" stroke="#4b5563" stroke-width="1" marker-end="url(#arr)"/>
        <rect x="328" y="406" width="236" height="34" rx="6" fill="#1c0a0a" stroke="#991b1b44" stroke-width="1"/>
        <text x="446" y="420" text-anchor="middle" fill="#6b7280" font-size="9">block / route_to_human</text>
        <text x="446" y="433" text-anchor="middle" fill="#f87171" font-size="9.5" font-weight="600">→ human review queue</text>
        <line x1="210" y1="442" x2="210" y2="458" stroke="#16a34a" stroke-width="1.5" marker-end="url(#arr-green)"/>

        <!-- POST -->
        <ellipse cx="210" cy="476" rx="72" ry="18" fill="#0d1f13" stroke="#16a34a" stroke-width="1.5"/>
        <text x="210" y="480" text-anchor="middle" fill="#22c55e" font-size="12" font-weight="700">POST ✓</text>
      </svg>
    </div>

  <!-- SPEC TAB -->
  {:else}
    <div class="spec-main-grid">

      <!-- Pipeline cards -->
      <div class="pipeline-col">
        <div class="section-title">Pipeline Stages</div>
        {#each pipeline as stage, i}
          <div class="stage" style="--border: {stage.border}; --bg: {stage.bg}">
            <div class="stage-header">
              <span class="stage-num">{String(i + 1).padStart(2, '0')}</span>
              <span class="stage-name" style="color: {stage.color}">{stage.label}</span>
              <span class="stage-model">{stage.model}</span>
            </div>
            <div class="stage-desc">{stage.desc}</div>
            <div class="stage-outputs">
              {#each stage.outputs as out}
                <span class="output-tag">{out}</span>
              {/each}
            </div>
          </div>
          {#if i < pipeline.length - 1}
            <div class="arrow">↓</div>
          {/if}
        {/each}
      </div>

      <!-- Tables -->
      <div class="tables-col">

        <div class="section-title">Routing Logic</div>
        <div class="spec-table">
          <div class="table-head">
            <span>Route</span><span>Trigger</span><span>Output</span>
          </div>
          {#each routes as r}
            <div class="table-row">
              <span class="route-chip">{r.route.replace(/_/g, ' ')}</span>
              <span class="td-trigger">{r.trigger}</span>
              <span class="td-output" class:auto={r.auto} class:human={!r.auto}>{r.output}</span>
            </div>
          {/each}
        </div>

        <div class="section-title" style="margin-top:20px">Guardrail & Escalation Rules</div>
        <div class="guard-table">
          {#each guardrails as g}
            <div class="guard-row">
              <div class="guard-rule">{g.rule}</div>
              <div class="guard-action">{g.action}</div>
              <div class="guard-detail">{g.detail}</div>
            </div>
          {/each}
        </div>

        <div class="box" style="margin-top:20px">
          <div class="box-title">Kill Switch</div>
          <div class="box-body">Set <code>KILL_SWITCH=1</code> in the environment. Agent immediately stops posting — all mentions return <code>paused</code> status. Designed for crisis situations. Resumes when flag is removed without restart.</div>
        </div>

        <div class="box" style="margin-top:12px">
          <div class="box-title">Human-in-the-Loop Checkpoints</div>
          <div class="hitl-grid">
            <div class="hitl-item">
              <div class="hitl-label">Always human</div>
              <div class="hitl-desc">Escalated complaints (acknowledge queues for follow-up). No-match retrievals. Copy review failures after max retries.</div>
            </div>
            <div class="hitl-item">
              <div class="hitl-label">Conditional</div>
              <div class="hitl-desc">Output guard route_to_human. Orchestrator returns unrecognized route. Any pipeline agent returns None.</div>
            </div>
            <div class="hitl-item">
              <div class="hitl-label">Agent acts alone</div>
              <div class="hitl-desc">All fixed replies. Clean deal_request + positive_response pipelines that pass output guard. Proactive deal drops and trend hooks.</div>
            </div>
          </div>
        </div>

      </div>
    </div>
  {/if}
</div>

<style>
  .arch {
    flex: 1;
    overflow-y: auto;
    padding: 24px 28px;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .page-header { display: flex; flex-direction: column; gap: 4px; }
  .page-title { font-size: 20px; font-weight: 700; color: var(--c-t1); }
  .page-sub { font-size: 12px; color: var(--c-t2); }

  /* Sub-tabs */
  .subtabs {
    display: flex;
    gap: 4px;
    border-bottom: 1px solid var(--c-border);
    padding-bottom: 0;
  }

  .subtab {
    background: none;
    border: none;
    color: var(--c-t2);
    font-size: 13px;
    padding: 8px 16px;
    cursor: pointer;
    position: relative;
    transition: color 0.15s;
  }
  .subtab:hover { color: var(--c-t1); }
  .subtab.active {
    color: var(--c-t1);
    font-weight: 500;
  }
  .subtab.active::after {
    content: '';
    position: absolute;
    bottom: -1px;
    left: 16px;
    right: 16px;
    height: 2px;
    background: var(--c-green);
    border-radius: 2px 2px 0 0;
  }

  /* Diagram — stays dark in both themes (hardcoded SVG colors) */
  .diagram-wrap {
    background: #0a0b0d;
    border: 1px solid #2f3336;
    border-radius: 14px;
    padding: 20px;
    overflow-x: auto;
  }
  .diagram {
    display: block;
    width: 100%;
    max-width: 680px;
    margin: 0 auto;
    height: auto;
  }

  /* Spec tab layout */
  .spec-main-grid {
    display: grid;
    grid-template-columns: 340px 1fr;
    gap: 24px;
    align-items: start;
  }

  .section-title {
    font-size: 11px;
    font-weight: 600;
    color: var(--c-t1);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 10px;
  }

  /* Pipeline cards */
  .pipeline-col { display: flex; flex-direction: column; }

  /* Stage card uses locally-scoped --bg and --border from inline style (dark values from JS data).
     In light mode we override the background to the neutral tile; border color stays semantic. */
  .stage {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  :global([data-theme="light"]) .stage {
    background: var(--c-tile);
  }

  .stage-header { display: flex; align-items: center; gap: 8px; }
  .stage-num { font-size: 10px; color: var(--c-t2); font-weight: 600; }
  .stage-name { font-size: 13px; font-weight: 700; flex: 1; }
  .stage-model { font-size: 10px; color: var(--c-t2); background: var(--c-tile); padding: 2px 6px; border-radius: 4px; white-space: nowrap; }
  .stage-desc { font-size: 11px; color: var(--c-t2); line-height: 1.5; }
  .stage-outputs { display: flex; flex-wrap: wrap; gap: 4px; }
  .output-tag { font-size: 10px; color: var(--c-t2); background: var(--c-row); border: 1px solid var(--c-border); padding: 2px 7px; border-radius: 4px; }

  .arrow { text-align: center; color: var(--c-border); font-size: 16px; line-height: 1.8; }

  /* Tables */
  .tables-col { display: flex; flex-direction: column; }

  .spec-table, .guard-table {
    background: var(--c-panel);
    border: 1px solid var(--c-border);
    border-radius: 12px;
    overflow: hidden;
    font-size: 12px;
  }

  .table-head {
    display: grid;
    grid-template-columns: 140px 1fr 160px;
    gap: 8px;
    padding: 8px 14px;
    background: var(--c-tile);
    color: var(--c-t2);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    border-bottom: 1px solid var(--c-border);
  }

  .table-row {
    display: grid;
    grid-template-columns: 140px 1fr 160px;
    gap: 8px;
    padding: 10px 14px;
    border-bottom: 1px solid var(--c-divider);
    align-items: start;
  }
  .table-row:last-child { border-bottom: none; }

  .route-chip { font-size: 11px; font-weight: 600; color: var(--c-t1); text-transform: capitalize; }
  .td-trigger { color: var(--c-t2); font-size: 11px; line-height: 1.4; }
  .td-output { font-size: 10px; font-weight: 500; padding: 3px 8px; border-radius: 6px; text-align: center; }
  .td-output.auto  { background: var(--c-green-s); color: var(--c-green); border: 1px solid var(--c-green-b); }
  .td-output.human { background: var(--c-yellow-s); color: var(--c-yellow); border: 1px solid var(--c-yellow-b); }

  .guard-row {
    display: grid;
    grid-template-columns: 180px 160px 1fr;
    gap: 12px;
    padding: 10px 14px;
    border-bottom: 1px solid var(--c-divider);
    font-size: 11px;
    align-items: start;
  }
  .guard-row:last-child { border-bottom: none; }
  .guard-rule   { color: var(--c-t1); font-weight: 500; }
  .guard-action { color: var(--c-red); font-size: 10px; }
  .guard-detail { color: var(--c-t2); line-height: 1.4; }

  .box {
    background: var(--c-panel);
    border: 1px solid var(--c-border);
    border-radius: 12px;
    padding: 16px;
  }
  .box-title { font-size: 11px; font-weight: 600; color: var(--c-t1); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 10px; }
  .box-body { font-size: 12px; color: var(--c-t2); line-height: 1.6; }
  .box-body code { background: var(--c-tile); padding: 1px 5px; border-radius: 4px; color: var(--c-t1); font-size: 11px; }

  .hitl-grid { display: flex; flex-direction: column; gap: 10px; }
  .hitl-item { display: flex; flex-direction: column; gap: 3px; }
  .hitl-label { font-size: 11px; font-weight: 600; color: var(--c-t1); }
  .hitl-desc { font-size: 11px; color: var(--c-t2); line-height: 1.5; }
</style>
