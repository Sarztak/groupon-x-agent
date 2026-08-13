import datetime
import json
from collections import Counter
from pathlib import Path

LOG_FILE          = "agent_log.jsonl"
POSTS_LOG_FILE    = "posts_log.jsonl"
REVIEW_QUEUE_FILE = "human_review_queue.jsonl"

# ── Baseline (illustrative scenario — not live Groupon figures) ───────────────
BASELINE_FOLLOWERS            = 120_000
BASELINE_POSTS_PER_WEEK       = 3         # 3 posts/week
BASELINE_SESSIONS_PER_MONTH   = 4_000     # assumed traffic from social posts
BASELINE_CONVERSION_VALUE     = 18_000    # USD/month, assumed
BASELINE_REPLY_RATE           = 0.10      # <10% of inbound mentions get a reply today
COORDINATOR_HOURLY_RATE       = 40        # USD/hr loaded rate, conservative US market

# ── Projection constants (capacity-based, not log-driven) ────────────────────
AGENT_DEAL_DROPS_PER_WEEK  = 4    # given ceiling — deals worth surfacing per week
AGENT_TREND_HOOKS_PER_WEEK = 3    # assumed opportunistic trend-aligned posts
WEEKS_PER_MONTH            = 4.33

# Derived baseline rates — use same WEEKS_PER_MONTH as agent projection for consistency
BASELINE_POSTS_PER_MONTH   = BASELINE_POSTS_PER_WEEK * WEEKS_PER_MONTH  # ~13
VALUE_PER_SESSION  = BASELINE_CONVERSION_VALUE / BASELINE_SESSIONS_PER_MONTH  # $4.50
SESSIONS_PER_POST  = BASELINE_SESSIONS_PER_MONTH / BASELINE_POSTS_PER_MONTH   # ~308

INBOUND_MENTIONS_PER_WEEK  = 100  # assumed for 120K-follower consumer brand
AGENT_REPLY_RATE           = 0.95 # ~95%: hard-blocks and true escalations excluded

# Only deal_request replies carry a link worth clicking.
# acknowledge (complaints) and positive_response replies have no deal — no click-through.
# Route mix from simulated mention data: deal_request ~35%, rest ~65%
DEAL_REQUEST_REPLY_FRACTION = 0.35

# Reply-to-session conversion applies only to deal_request replies
# Reach per reply = ~5 people (recipient + thread viewers)
# CTR among those = 15% (direct/relevant context, higher than passive feed)
REPLY_REACH        = 5
REPLY_CTR          = 0.15
SESSIONS_PER_REPLY = REPLY_REACH * REPLY_CTR  # = 0.75

# ── Time saved per action (execution only) ───────────────────────────────────
# Covers: drafting + posting time. Does NOT cover coordination, reporting,
# or escalation handling — those may increase with agent (more coverage = more escalations).
# mention reply: read + draft + post
# deal/trend post: select deal + draft copy + schedule
MINS_PER_MENTION_REPLY = 5
MINS_PER_DEAL_DROP     = 30   # realistic drafting time with brand voice
MINS_PER_TREND_HOOK    = 30

# ── Estimated API cost per action — Sonnet 4.6 with prompt caching ───────────
# Actual system prompt sizes (bytes → tokens at ~4 chars/token):
#   input_guard:   4,474 B → ~1,100 tok   output_guard:   6,659 B → ~1,650 tok
#   orchestrator:  5,871 B → ~1,470 tok   conversational: 4,692 B → ~1,170 tok
#   copywriter:   19,569 B → ~4,900 tok   reviewer:      21,676 B → ~5,400 tok
#   retrieval:     1,576 B →   ~394 tok
# Pricing: Sonnet 4.6 — $3/MTok input, $11.25/MTok cache-write, $15/MTok output.
# Cache TTL is 5 min; at realistic prod cadence every call is a cold write — no warm reads assumed.
# Measured (cold): input_guard $0.015, copywriter $0.061, reviewer $0.070, output_guard $0.022.
# Orchestrator, retrieval, conversational estimated at ~$0.020 each (unmeasured, similar prompt size to input_guard).
API_COST_BY_ROUTE = {
    "blocked_reply":     0.015,   # input_guard only (1 call, measured)
    "sensitive_block":   0.015,   # input_guard only (1 call, measured)
    "off_topic":         0.035,   # input_guard + orchestrator (2 calls)
    "acknowledge":       0.075,   # input_guard + orchestrator + conversational + output_guard (4 calls)
    "positive_response": 0.075,   # same (4 calls)
    "deal_request":      0.220,   # full pipeline: all 7 calls ($0.168 measured + ~$0.05 estimated for 3 CLI calls)
    "deal_drop":         0.150,   # copywriter + reviewer + output_guard (3 calls, measured)
    "trend_hook":        0.150,   # copywriter + reviewer + output_guard (3 calls, same as deal_drop)
}
API_COST_ESCALATED_USD = 0.035   # input_guard + orchestrator before escalation (2 calls)

# ── Build & run cost ─────────────────────────────────────────────────────────
ENGINEER_HOURLY_RATE  = 60              # USD/hr, junior-level engineer loaded rate
BUILD_HOURS_RANGE     = (150, 200)      # estimated engineering hours to productionize
BUILD_COST_LOW_USD    = BUILD_HOURS_RANGE[0] * ENGINEER_HOURLY_RATE
BUILD_COST_HIGH_USD   = BUILD_HOURS_RANGE[1] * ENGINEER_HOURLY_RATE
MONTHLY_RUN_COST_USD = 55       # estimated API spend at projection volume (cold-cache pricing, all Sonnet 4.6)
# Derivation: ~17 deal_drops ($2.60) + ~13 trend_hooks ($1.95) + ~411 handled mentions
# (144 deal_request × $0.22 + 123 acknowledge × $0.075 + 103 positive × $0.075 + 42 blocked/off_topic × $0.025 avg)
# = $54 → rounded to $55


def read_jsonl(path: str) -> list[dict]:
    if not Path(path).exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def log_event(event: str, **fields):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "event": event,
            **fields,
        }) + "\n")


def log_post(post_type: str, route: str, copy: str):
    with open(POSTS_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "type": post_type,   # mention_reply | deal_drop | trend_hook
            "route": route,
            "copy": copy
        }) + "\n")


def _build_projection() -> dict:
    """Monthly projection from capacity constants — not log-driven."""
    proactive_posts_month = (AGENT_DEAL_DROPS_PER_WEEK + AGENT_TREND_HOOKS_PER_WEEK) * WEEKS_PER_MONTH
    sessions_from_posts   = proactive_posts_month * SESSIONS_PER_POST

    inbound_month          = INBOUND_MENTIONS_PER_WEEK * WEEKS_PER_MONTH
    agent_replies          = inbound_month * AGENT_REPLY_RATE
    deal_request_replies   = agent_replies * DEAL_REQUEST_REPLY_FRACTION
    sessions_from_replies  = deal_request_replies * SESSIONS_PER_REPLY

    total_sessions        = sessions_from_posts + sessions_from_replies
    conversion_value      = total_sessions * VALUE_PER_SESSION

    hours_saved_posts     = proactive_posts_month * (MINS_PER_DEAL_DROP / 60)
    hours_saved_replies   = agent_replies * (MINS_PER_MENTION_REPLY / 60)
    hours_saved_total     = round(hours_saved_posts + hours_saved_replies, 1)
    cost_saved            = round(hours_saved_total * COORDINATOR_HOURLY_RATE, 2)

    net_labor_monthly  = cost_saved - MONTHLY_RUN_COST_USD
    net_full_monthly   = cost_saved + round(conversion_value, 2) - MONTHLY_RUN_COST_USD

    payback = {
        "conservative": {
            "basis":    f"hours saved only — ${ENGINEER_HOURLY_RATE}/hr × {BUILD_HOURS_RANGE[0]}–{BUILD_HOURS_RANGE[1]}h",
            "low_months":  round(BUILD_COST_LOW_USD  / net_labor_monthly, 1),
            "high_months": round(BUILD_COST_HIGH_USD / net_labor_monthly, 1),
        },
        "full": {
            "basis":    "hours saved + conversion uplift (dependent on unverified session→revenue assumption)",
            "low_days":  round((BUILD_COST_LOW_USD  / net_full_monthly) * 30.4),
            "high_days": round((BUILD_COST_HIGH_USD / net_full_monthly) * 30.4),
        },
        "build_cost_low_usd":    BUILD_COST_LOW_USD,
        "build_cost_high_usd":   BUILD_COST_HIGH_USD,
        "engineer_hourly_rate":  ENGINEER_HOURLY_RATE,
        "build_hours_low":       BUILD_HOURS_RANGE[0],
        "build_hours_high":      BUILD_HOURS_RANGE[1],
        "monthly_run_cost_usd":  MONTHLY_RUN_COST_USD,
        "monthly_labor_value":   cost_saved,
        "monthly_conversion_uplift": round(conversion_value, 2),
        "total_monthly_benefit": round(cost_saved + conversion_value, 2),
    }

    return {
        "proactive_posts_per_month":         round(proactive_posts_month, 1),
        "deal_drops_per_month":              round(AGENT_DEAL_DROPS_PER_WEEK * WEEKS_PER_MONTH, 1),
        "trend_hooks_per_month":             round(AGENT_TREND_HOOKS_PER_WEEK * WEEKS_PER_MONTH, 1),
        "inbound_mentions_per_month":        round(inbound_month),
        "agent_replies_per_month":           round(agent_replies),
        "deal_request_replies_per_month":    round(deal_request_replies),
        "sessions_from_posts":               round(sessions_from_posts),
        "sessions_from_replies":             round(sessions_from_replies),
        "total_new_sessions":           round(total_sessions),
        "conversion_value_usd":         round(conversion_value, 2),
        "hours_saved":                  hours_saved_total,
        "cost_saved_usd":               cost_saved,
        "payback":                      payback,
        "assumptions": {
            "deal_drops_per_week":        AGENT_DEAL_DROPS_PER_WEEK,
            "trend_hooks_per_week":       AGENT_TREND_HOOKS_PER_WEEK,
            "inbound_mentions_per_week":  INBOUND_MENTIONS_PER_WEEK,
            "agent_reply_rate":           AGENT_REPLY_RATE,
            "sessions_per_post":          round(SESSIONS_PER_POST, 1),
            "deal_request_reply_fraction": DEAL_REQUEST_REPLY_FRACTION,
            "sessions_per_reply":         SESSIONS_PER_REPLY,
            "reply_reach":                REPLY_REACH,
            "reply_ctr":                  REPLY_CTR,
            "value_per_session_usd":      VALUE_PER_SESSION,
            "coordinator_hourly_rate":    COORDINATOR_HOURLY_RATE,
        }
    }


def summarize(since: datetime.datetime | None = None) -> dict:
    posts        = read_jsonl(POSTS_LOG_FILE)
    escalations  = read_jsonl(REVIEW_QUEUE_FILE)
    guard_events = read_jsonl(LOG_FILE)

    if since:
        iso          = since.isoformat()
        posts        = [p for p in posts        if p["timestamp"] >= iso]
        escalations  = [e for e in escalations  if e["timestamp"] >= iso]
        guard_events = [e for e in guard_events if e["timestamp"] >= iso]

    # ── Activity (log-driven) ────────────────────────────────────────────────
    mention_replies = [p for p in posts if p["type"] == "mention_reply"]
    deal_drops      = [p for p in posts if p["type"] == "deal_drop"]
    trend_hooks     = [p for p in posts if p["type"] == "trend_hook"]

    content_posts   = len(deal_drops) + len(trend_hooks)   # proactive only — replies don't drive feed traffic
    total_escalated = len(escalations)

    input_guard_events  = [e for e in guard_events if e.get("guard") == "input_guard"]
    total_mentions_seen = len(input_guard_events)
    reply_rate          = len(mention_replies) / total_mentions_seen if total_mentions_seen else 0

    routes = Counter(p["route"] for p in mention_replies)

    # Sessions: proactive posts drive feed traffic; only deal_request replies carry a link
    deal_request_replies  = routes.get("deal_request", 0)
    sessions_from_posts   = content_posts * SESSIONS_PER_POST
    sessions_from_replies = deal_request_replies * SESSIONS_PER_REPLY
    total_sessions        = sessions_from_posts + sessions_from_replies
    conversion_value      = round(total_sessions * VALUE_PER_SESSION, 2)

    # Hours saved: execution time only
    mins_saved   = (
        len(mention_replies) * MINS_PER_MENTION_REPLY +
        len(deal_drops)      * MINS_PER_DEAL_DROP +
        len(trend_hooks)     * MINS_PER_TREND_HOOK
    )
    hours_saved    = round(mins_saved / 60, 1)
    cost_saved_usd = round(hours_saved * COORDINATOR_HOURLY_RATE, 2)

    # API cost
    api_cost_posts       = sum(API_COST_BY_ROUTE.get(p["route"], 0.010) for p in posts)
    api_cost_escalations = total_escalated * API_COST_ESCALATED_USD
    total_api_cost       = round(api_cost_posts + api_cost_escalations, 4)

    reply_rate_lift = round(reply_rate - BASELINE_REPLY_RATE, 3) if total_mentions_seen else 0

    return {
        "period": {
            "since":        since.isoformat() if since else "all time",
            "generated_at": datetime.datetime.now(datetime.UTC).isoformat()
        },
        "projection": _build_projection(),
        "activity": {
            "note": "Reflects agent runs in this session — test telemetry, not production data",
            "mention_replies_sent":     len(mention_replies),
            "deal_drops_published":     len(deal_drops),
            "trend_hooks_published":    len(trend_hooks),
            "total_posts_published":    len(posts),
            "total_mentions_seen":      total_mentions_seen,
            "total_escalated_to_human": total_escalated,
            "reply_rate":               round(reply_rate, 3),
            "reply_rate_baseline":      BASELINE_REPLY_RATE,
            "reply_rate_lift":          reply_rate_lift,
            "by_route":                 dict(routes),
            "sessions_from_posts":      round(sessions_from_posts),
            "sessions_from_replies":    round(sessions_from_replies),
            "total_sessions":           round(total_sessions),
            "conversion_value_usd":     conversion_value,
            "hours_saved":              hours_saved,
            "cost_saved_usd":           cost_saved_usd,
            "api_cost": {
                "total_usd":       total_api_cost,
                "posts_usd":       round(api_cost_posts, 4),
                "escalations_usd": round(api_cost_escalations, 4),
            }
        },
        "baselines": {
            "note":                          "Illustrative scenario data — not live Groupon figures",
            "followers":                     BASELINE_FOLLOWERS,
            "baseline_posts_per_month":      BASELINE_POSTS_PER_MONTH,
            "baseline_sessions_per_month":   BASELINE_SESSIONS_PER_MONTH,
            "baseline_conversion_value_usd": BASELINE_CONVERSION_VALUE,
            "baseline_reply_rate":           BASELINE_REPLY_RATE,
        }
    }


if __name__ == "__main__":
    s = summarize()
    p = s["projection"]
    a = s["activity"]
    pb = p["payback"]

    print("\n── Projection (capacity-based, monthly) ──")
    print(f"Proactive posts/month:    {p['proactive_posts_per_month']}  ({p['deal_drops_per_month']} deal drops + {p['trend_hooks_per_month']} trend hooks)")
    print(f"Replies/month:            {p['agent_replies_per_month']}  ({p['inbound_mentions_per_month']} inbound × {AGENT_REPLY_RATE:.0%} reply rate)")
    print(f"Sessions from posts:      {p['sessions_from_posts']:,}")
    print(f"Sessions from replies:    {p['sessions_from_replies']:,}  ({SESSIONS_PER_REPLY} sessions/reply: {REPLY_REACH} reach × {REPLY_CTR} CTR)")
    print(f"Total new sessions:       {p['total_new_sessions']:,}")
    print(f"Est. conversion value:    ${p['conversion_value_usd']:,.0f}/month")
    print(f"Hours saved (execution):  {p['hours_saved']}h  (${p['cost_saved_usd']:,.0f})")

    print("\n── Build & Payback ──")
    print(f"Engineer rate:            ${ENGINEER_HOURLY_RATE}/hr  ·  estimate {BUILD_HOURS_RANGE[0]}–{BUILD_HOURS_RANGE[1]}h")
    print(f"Build cost range:         ${pb['build_cost_low_usd']:,.0f}–${pb['build_cost_high_usd']:,.0f}")
    print(f"Monthly run cost:         ${pb['monthly_run_cost_usd']}")
    print(f"Monthly labor value:      ${pb['monthly_labor_value']:,.0f}  ·  total benefit ${pb['total_monthly_benefit']:,.0f}")
    print(f"Conservative payback:     {pb['conservative']['low_months']}–{pb['conservative']['high_months']} months  ({pb['conservative']['basis']})")
    print(f"Full payback:             {pb['full']['low_days']}–{pb['full']['high_days']} days  ({pb['full']['basis']})")

    print("\n── Activity (log telemetry — test env) ──")
    print(f"Deal drops:               {a['deal_drops_published']}")
    print(f"Trend hooks:              {a['trend_hooks_published']}")
    print(f"Mention replies:          {a['mention_replies_sent']}  (by route: {dict(a['by_route'])})")
    print(f"Escalated to human:       {a['total_escalated_to_human']}")
    print(f"Sessions (derived):       {a['total_sessions']:,}  →  ${a['conversion_value_usd']:,.0f}")
    print(f"Hours saved (execution):  {a['hours_saved']}h  (${a['cost_saved_usd']:,.0f})")
    print(f"API spend:                ${a['api_cost']['total_usd']:,.4f}")
    print(f"\n* {s['baselines']['note']}")
