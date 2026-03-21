"""AI-humanization input enhancements for EVOLV.

Provides two ambient intelligence features:

1. **Ghost Text** — as the user types in a requirement field, a
   faint gray completion suggestion appears after their cursor.
   Pressing Tab accepts the suggestion. No button needed.

2. **Selection Toolbar** — when the user highlights any text in a
   textarea, a small floating menu appears above the selection
   with two Notion-style actions:
     · ✦ Make SMART  — rewrites to 'The system shall...' format
     · ⚡ Analyze Impact — copies for use in Blast Radius page

Both features inject JavaScript directly into the parent
Streamlit document via ``streamlit.components.v1.html()`` using
the ``parent.document`` cross-frame technique.

Usage::

    from components.ai_input import (
        attach_ghost_text,
        attach_selection_toolbar,
    )

    # After any st.text_area(..., key="p2_requirement"):
    attach_ghost_text("Requirement description")

    # Once per page to enable global selection menu:
    attach_selection_toolbar()

:requirement: URS-21.3 - Rewrite vague requirements to SMART format.
"""

import streamlit.components.v1 as components


# ── Ghost Text ────────────────────────────────────────────────────

_GHOST_PHRASES = [
    "The system shall ",
    "The system shall enforce ",
    "The system shall record ",
    "The system shall notify ",
    "The system shall validate ",
    "The system shall prevent ",
    "The system shall provide ",
    "The system shall maintain ",
]

_VAGUE_WORDS = [
    "easily", "quickly", "efficiently", "appropriately",
    "suitably", "properly", "adequately", "generally",
    "often", "usually", "sometimes", "in a timely manner",
]


def attach_ghost_text(
    textarea_label: str,
    min_chars: int = 3,
) -> None:
    """Attach ghost-text completion to a Streamlit textarea.

    Targets the textarea by its ``aria-label`` (which Streamlit sets
    to the label string passed to ``st.text_area``).

    After the user types ``min_chars`` characters:
    - If the text does not start with "The system shall", the ghost
      text suggests "The system shall {typed_text}".
    - If the typed text matches a known vague phrase, a SMART
      replacement is suggested.
    - Pressing **Tab** accepts the suggestion by splicing it into
      the textarea value and triggering React's synthetic onChange.

    A subtle "Tab ↹" hint badge appears at the bottom-right of the
    field when a suggestion is active.

    :param textarea_label: The label passed to ``st.text_area()``.
    :param min_chars: Minimum characters before suggestions appear.
    :requirement: URS-21.3 - Rewrite vague requirements to SMART.
    """
    # Escape the label for safe JS string embedding
    safe_label = (
        textarea_label
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("'", "\\'")
        .replace("\n", " ")
    )
    vague_list_js = (
        "[" + ",".join(f'"{w}"' for w in _VAGUE_WORDS) + "]"
    )

    components.html(
        f"""
        <script>
        (function() {{
          var LABEL      = "{safe_label}";
          var MIN_CHARS  = {min_chars};
          var VAGUE      = {vague_list_js};

          function getSuggestion(val) {{
            if (!val || val.length < MIN_CHARS) return "";
            var v = val.trim();
            // Already a well-formed shall statement
            if (/^the system shall /i.test(v)) {{
              // Check for vague words
              for (var i = 0; i < VAGUE.length; i++) {{
                if (v.toLowerCase().includes(VAGUE[i])) {{
                  return " [⚠ vague: consider replacing '"
                         + VAGUE[i] + "']";
                }}
              }}
              return "";
            }}
            // Suggest the shall prefix completion
            var completion = "The system shall "
              + v.charAt(0).toLowerCase() + v.slice(1);
            if (!completion.endsWith('.')) completion += '.';
            // Ghost shows only the missing suffix
            return completion.slice(v.length);
          }}

          function setNativeValue(el, value) {{
            var setter = Object.getOwnPropertyDescriptor(
              window.HTMLTextAreaElement.prototype, 'value'
            ).set;
            setter.call(el, value);
            el.dispatchEvent(new Event('input', {{bubbles: true}}));
          }}

          function attach() {{
            var ta = parent.document.querySelector(
              'textarea[aria-label="' + LABEL + '"]'
            );
            if (!ta || ta._evGhostAttached) return;
            ta._evGhostAttached = true;

            // ── Build hint badge ────────────────────────────────
            var hint = parent.document.createElement('div');
            hint.textContent = 'Tab ↹ to accept';
            hint.style.cssText = [
              'position:absolute',
              'bottom:6px',
              'right:10px',
              'background:var(--ev-bg-alt, #F1F5F9)',
              'border:1px solid var(--ev-border, #E2E8F0)',
              'border-radius:4px',
              'padding:1px 7px',
              'font-size:11px',
              'font-weight:600',
              'color:var(--ev-slate-light, #64748B)',
              'letter-spacing:.04em',
              'pointer-events:none',
              'z-index:20',
              'opacity:0',
              'transition:opacity .15s',
              'font-family:inherit',
            ].join(';');

            // ── Wrap textarea in a positioned container ──────────
            var wrapper = ta.parentNode;
            if (wrapper && wrapper.style) {{
              wrapper.style.position = 'relative';
            }}
            if (wrapper) wrapper.appendChild(hint);

            // ── Ghost text overlay div ───────────────────────────
            var ghost = parent.document.createElement('div');
            ghost.style.cssText = [
              'position:absolute',
              'inset:0',
              'pointer-events:none',
              'padding:10px 14px',
              'font-family:inherit',
              'font-size:15px',
              'line-height:1.65',
              'color:transparent',
              'white-space:pre-wrap',
              'word-break:break-word',
              'overflow:hidden',
              'z-index:1',
            ].join(';');

            var ghostSpan = parent.document.createElement('span');
            ghostSpan.style.cssText = [
              'color:#CBD5E1',
              'font-style:italic',
            ].join(';');
            ghost.appendChild(ghostSpan);
            if (wrapper) wrapper.appendChild(ghost);

            // ── Event: input ─────────────────────────────────────
            ta.addEventListener('input', function() {{
              var sugg = getSuggestion(ta.value);
              if (sugg) {{
                // The ghost div contains existing text (transparent)
                // + the suggestion (slate-300)
                ghost.childNodes[0] && ghost.removeChild(
                  ghost.childNodes[0]
                );
                var textNode = parent.document.createTextNode(
                  ta.value
                );
                ghost.insertBefore(textNode, ghostSpan);
                ghostSpan.textContent = sugg;
                hint.style.opacity = '1';
              }} else {{
                ghost.childNodes[0]
                  && ghost.childNodes[0].nodeType === 3
                  && ghost.removeChild(ghost.childNodes[0]);
                ghostSpan.textContent = '';
                hint.style.opacity = '0';
              }}
            }});

            // ── Event: Tab to accept ─────────────────────────────
            ta.addEventListener('keydown', function(e) {{
              if (e.key !== 'Tab') return;
              var sugg = ghostSpan.textContent;
              if (!sugg || sugg.startsWith(' [⚠')) return;
              e.preventDefault();
              var newVal = ta.value + sugg;
              setNativeValue(ta, newVal);
              ghostSpan.textContent = '';
              ghost.childNodes[0]
                && ghost.childNodes[0].nodeType === 3
                && ghost.removeChild(ghost.childNodes[0]);
              hint.style.opacity = '0';
              // Move cursor to end
              ta.selectionStart = ta.selectionEnd = newVal.length;
            }});

            // ── Event: blur — hide hint ──────────────────────────
            ta.addEventListener('blur', function() {{
              hint.style.opacity = '0';
            }});
          }}

          // Retry loop: Streamlit renders async
          attach();
          setTimeout(attach, 250);
          setTimeout(attach, 700);
          setTimeout(attach, 1500);
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


# ── Selection Toolbar ─────────────────────────────────────────────

def attach_selection_toolbar() -> None:
    """Inject the global floating selection toolbar.

    When the user selects text (≥ 10 chars) in any textarea on the
    page, a dark pill appears just above the selection with:

    · **✦ Make SMART** — rewrites selected text to
      "The system shall …" SMART format in place.
    · **⚡ Analyze Impact** — copies text to clipboard and shows
      a toast: "Copied — navigate to Blast Radius to analyse."

    Safe to call once per page; uses a guard flag to prevent
    double-injection across reruns.

    :requirement: URS-21.3 - Rewrite vague requirements to SMART.
    """
    components.html(
        r"""
        <script>
        (function() {
          // Guard: only attach once per parent document load
          if (parent.__evolvSelToolbar) return;
          parent.__evolvSelToolbar = true;

          // ── Build toolbar DOM ───────────────────────────────────
          var bar = parent.document.createElement('div');
          bar.className = 'evolv-selection-toolbar';
          bar.style.cssText = [
            'position:fixed',
            'z-index:99999',
            'display:none',
            'align-items:center',
            'gap:2px',
            'background:#1E293B',
            'border:1px solid rgba(255,255,255,0.10)',
            'border-radius:8px',
            'padding:3px 4px',
            'box-shadow:0 8px 24px rgba(0,0,0,0.25)',
            'pointer-events:auto',
          ].join(';');

          function makeBtn(icon, label, action) {
            var b = parent.document.createElement('button');
            b.style.cssText = [
              'display:flex',
              'align-items:center',
              'gap:5px',
              'background:transparent',
              'border:none',
              'border-radius:5px',
              'padding:5px 9px',
              'font-family:inherit',
              'font-size:12px',
              'font-weight:600',
              'color:#E2E8F0',
              'cursor:pointer',
              'white-space:nowrap',
              'letter-spacing:.01em',
              'transition:background .1s',
            ].join(';');
            b.innerHTML = '<span style="font-size:11px;opacity:.85">'
              + icon + '</span>'
              + '<span>' + label + '</span>';
            b.onmouseover = function() {
              b.style.background = 'rgba(255,255,255,.10)';
            };
            b.onmouseout = function() {
              b.style.background = 'transparent';
            };
            b.dataset.action = action;
            return b;
          }

          var divider = parent.document.createElement('div');
          divider.style.cssText =
            'width:1px;height:16px;background:rgba(255,255,255,.15);'
            + 'flex-shrink:0;margin:0 2px;';

          var btnSmart  = makeBtn('\u2736', 'Make SMART',      'smart');
          var btnImpact = makeBtn('\u26A1', 'Analyze Impact',  'impact');

          bar.appendChild(btnSmart);
          bar.appendChild(divider);
          bar.appendChild(btnImpact);
          parent.document.body.appendChild(bar);

          var _activeTA  = null;
          var _selStart  = 0;
          var _selEnd    = 0;

          // ── Toast helper ────────────────────────────────────────
          function toast(msg) {
            var t = parent.document.createElement('div');
            t.className = 'evolv-toast entering';
            t.style.cssText = [
              'position:fixed',
              'bottom:24px',
              'right:24px',
              'background:#1E293B',
              'color:#F1F5F9',
              'padding:10px 16px',
              'border-radius:8px',
              'font-family:inherit',
              'font-size:13px',
              'font-weight:500',
              'z-index:100000',
              'box-shadow:0 4px 16px rgba(0,0,0,.25)',
              'border:1px solid rgba(255,255,255,.10)',
              'max-width:320px',
              'line-height:1.5',
              'pointer-events:none',
              'animation:toast-in .2s ease forwards',
            ].join(';');
            t.textContent = msg;
            parent.document.body.appendChild(t);
            setTimeout(function() {
              t.style.animation = 'toast-out .2s ease forwards';
              setTimeout(function() { t.remove(); }, 220);
            }, 3000);
          }

          // ── SMART transformation ─────────────────────────────────
          function toSmart(text) {
            var t = text.trim();
            if (!/^the system shall /i.test(t)) {
              t = 'The system shall '
                + t.charAt(0).toLowerCase() + t.slice(1);
            }
            // Remove vague qualifiers
            var VAGUE = [
              'easily','quickly','efficiently','appropriately',
              'suitably','properly','adequately','generally',
              'in a timely manner',
            ];
            VAGUE.forEach(function(w) {
              t = t.replace(new RegExp('\\b' + w + '\\b', 'gi'), '');
            });
            t = t.replace(/\s{2,}/g, ' ').trim();
            if (!t.endsWith('.')) t += '.';
            return t;
          }

          // ── Make SMART action ────────────────────────────────────
          function doMakeSmart() {
            if (!_activeTA) return;
            var start = _selStart;
            var end   = _selEnd;
            var orig  = _activeTA.value;
            var sel   = orig.substring(start, end);
            if (!sel) return;
            var smart = toSmart(sel);
            var newVal = orig.substring(0, start) + smart
                       + orig.substring(end);
            // Trigger React synthetic change
            var setter = Object.getOwnPropertyDescriptor(
              parent.HTMLTextAreaElement.prototype, 'value'
            ).set;
            setter.call(_activeTA, newVal);
            _activeTA.dispatchEvent(
              new Event('input', {bubbles: true})
            );
            _activeTA.selectionStart = start;
            _activeTA.selectionEnd   = start + smart.length;
            toast('\u2736 SMART — "The system shall…" applied');
            hideBar();
          }

          // ── Analyze Impact action ────────────────────────────────
          function doAnalyzeImpact() {
            var sel = parent.document.getSelection();
            var text = sel ? sel.toString().trim() : '';
            if (!text && _activeTA) {
              text = _activeTA.value.substring(_selStart, _selEnd);
            }
            if (text && parent.navigator.clipboard) {
              parent.navigator.clipboard.writeText(text)
                .catch(function() {});
            }
            toast(
              '\u26A1 Copied \u2014 navigate to Blast Radius'
              + ' to analyse this requirement\u2019s impact.'
            );
            hideBar();
          }

          // ── Show / hide bar ──────────────────────────────────────
          function showBar(x, y) {
            bar.style.display = 'flex';
            // Keep within viewport
            var bw = 200;
            var vw = parent.window.innerWidth;
            var cx = Math.min(Math.max(x - bw / 2, 8), vw - bw - 8);
            bar.style.left = cx + 'px';
            bar.style.top  = (y - 48) + 'px';
          }

          function hideBar() {
            bar.style.display = 'none';
          }

          // ── Button clicks ────────────────────────────────────────
          btnSmart.addEventListener('mousedown', function(e) {
            e.preventDefault();
            doMakeSmart();
          });
          btnImpact.addEventListener('mousedown', function(e) {
            e.preventDefault();
            doAnalyzeImpact();
          });

          // ── Track selection ──────────────────────────────────────
          parent.document.addEventListener('mouseup', function(e) {
            if (bar.contains(e.target)) return;
            setTimeout(function() {
              // Only activate inside a textarea
              var target = e.target;
              if (target.tagName !== 'TEXTAREA') {
                var docSel = parent.document.getSelection();
                if (!docSel || docSel.toString().trim().length < 10) {
                  hideBar();
                  return;
                }
                return;
              }
              var start = target.selectionStart;
              var end   = target.selectionEnd;
              if (end - start < 10) { hideBar(); return; }
              _activeTA = target;
              _selStart = start;
              _selEnd   = end;
              // Position near the selection
              var rect = target.getBoundingClientRect();
              // Approximate mid-x of selection inside textarea
              var midX = rect.left + rect.width / 2;
              showBar(midX, rect.top + parent.scrollY);
            }, 60);
          });

          // Hide on outside click
          parent.document.addEventListener('mousedown', function(e) {
            if (!bar.contains(e.target)) hideBar();
          });

          // Hide on scroll
          parent.document.addEventListener('scroll', hideBar, true);

        })();
        </script>
        """,
        height=0,
        width=0,
    )
