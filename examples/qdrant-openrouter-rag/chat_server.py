#!/usr/bin/env python3
"""
Interactive Web Chat Interface for RAGLens + Qdrant + OpenRouter RAG.

Serves an ultra-modern, dark-themed responsive chat web application
integrating real Qdrant vector retrieval, real OpenRouter generation,
and live RAGLens trace inspection links.

Usage:
    python examples/qdrant-openrouter-rag/chat_server.py
    # Open http://localhost:8501 in your browser
"""

import argparse
import asyncio
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

# Add current directory to path
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

load_dotenv(current_dir / ".env")

from pipeline import RAGPipeline

app = FastAPI(title="BookMyShow RAGLens Chat", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline: Optional[RAGPipeline] = None


@app.on_event("startup")
def startup():
    global pipeline
    pipeline = RAGPipeline()
    pipeline.ensure_indexed()


class ChatRequest(BaseModel):
    query: str
    top_k: int = 4
    confidence_threshold: float = 0.35


class ChatResponse(BaseModel):
    query: str
    answer: str
    trace_id: Optional[str] = None
    trace_url: Optional[str] = None
    status: str
    duration_ms: int
    metrics: Dict[str, Any]
    retrieval: List[Dict[str, Any]]
    qdrant_mode: str


@app.get("/api/status")
def get_status():
    global pipeline
    if not pipeline:
        pipeline = RAGPipeline()
    return {
        "qdrant": {
            "mode": pipeline.store.mode,
            "collection": pipeline.store.collection_name,
            "url": pipeline.store.url or "Embedded Local Storage",
            "indexed_count": pipeline.store.count(),
        },
        "openrouter": {
            "embedding_model": os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
            "chat_model": os.getenv("CHAT_MODEL", "openai/gpt-4o-mini"),
        },
        "raglens": {
            "enabled": pipeline.raglens.enabled,
            "project_id": pipeline.raglens.project_id,
            "web_url": pipeline.raglens.web_url,
            "dashboard_url": f"{pipeline.raglens.web_url}/projects/{pipeline.raglens.project_id}/traces",
        },
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    global pipeline
    if not pipeline:
        pipeline = RAGPipeline()

    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    def _execute():
        return pipeline.run(
            query=query,
            top_k=req.top_k,
            confidence_threshold=req.confidence_threshold,
        )

    answer, trace, results = await run_in_threadpool(_execute)

    trace_url = (
        trace.url
        if (trace and trace.url)
        else (
            f"{pipeline.raglens.web_url}/projects/{pipeline.raglens.project_id}/traces/{trace.id}"
            if (trace and trace.id)
            else None
        )
    )

    return ChatResponse(
        query=query,
        answer=answer,
        trace_id=trace.id if trace else None,
        trace_url=trace_url,
        status=trace.status if trace else "success",
        duration_ms=trace.duration_ms if trace else 0,
        metrics=trace.metrics if trace else {},
        retrieval=results,
        qdrant_mode=pipeline.store.mode,
    )


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>BookMyShow AI Assistant — RAGLens + Qdrant + OpenRouter</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" />
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: {
              50: '#f0fdf4',
              500: '#10b981',
              600: '#059669',
            },
          }
        }
      }
    }
  </script>
  <style>
    /* Custom scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #09090b; }
    ::-webkit-scrollbar-thumb { background: #27272a; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #3f3f46; }
    .prose pre { background-color: #18181b; padding: 0.75rem; border-radius: 0.5rem; }
    .prose code { color: #38bdf8; }
  </style>
</head>
<body class="bg-zinc-950 text-zinc-100 flex h-screen overflow-hidden font-sans antialiased selection:bg-emerald-500/30 selection:text-emerald-200">

  <!-- ── Left Sidebar (Configuration & Status) ────────────────────────────── -->
  <aside class="w-80 border-r border-zinc-800/80 bg-zinc-900/50 flex flex-col shrink-0 justify-between">
    <div class="p-5 space-y-6 overflow-y-auto">
      
      <!-- App Brand -->
      <div class="flex items-center gap-3">
        <div class="h-10 w-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20 text-white font-bold text-lg">
          <i class="fa-solid fa-film"></i>
        </div>
        <div>
          <h1 class="font-semibold text-sm tracking-tight text-white flex items-center gap-2">
            BookMyShow Bot
            <span class="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">LIVE</span>
          </h1>
          <p class="text-xs text-zinc-400">RAGLens Observability Demo</p>
        </div>
      </div>

      <!-- Live Service Status Cards -->
      <div class="space-y-3">
        <p class="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">Connected Infrastructure</p>
        
        <!-- Qdrant Card -->
        <div class="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3 space-y-1.5 text-xs">
          <div class="flex items-center justify-between">
            <span class="font-medium text-zinc-300 flex items-center gap-1.5">
              <i class="fa-solid fa-database text-sky-400"></i> Qdrant Vector DB
            </span>
            <span id="qdrant-mode-badge" class="px-1.5 py-0.5 rounded text-[10px] bg-sky-500/10 text-sky-400 border border-sky-500/20 uppercase font-mono">Loading...</span>
          </div>
          <div class="text-[11px] text-zinc-400 flex justify-between">
            <span>Collection:</span>
            <span id="qdrant-col" class="font-mono text-zinc-300">bookmyshow_rag</span>
          </div>
          <div class="text-[11px] text-zinc-400 flex justify-between">
            <span>Points Indexed:</span>
            <span id="qdrant-count" class="font-mono text-emerald-400 font-semibold">-</span>
          </div>
        </div>

        <!-- OpenRouter Card -->
        <div class="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3 space-y-1.5 text-xs">
          <div class="flex items-center justify-between">
            <span class="font-medium text-zinc-300 flex items-center gap-1.5">
              <i class="fa-solid fa-brain text-purple-400"></i> OpenRouter AI
            </span>
            <span class="px-1.5 py-0.5 rounded text-[10px] bg-purple-500/10 text-purple-400 border border-purple-500/20 font-mono">ACTIVE</span>
          </div>
          <div class="text-[11px] text-zinc-400 flex justify-between">
            <span>Embedding:</span>
            <span class="font-mono text-zinc-300 truncate max-w-[130px]" title="text-embedding-3-small">text-emb-3-small</span>
          </div>
          <div class="text-[11px] text-zinc-400 flex justify-between">
            <span>Chat Model:</span>
            <span class="font-mono text-zinc-300 truncate max-w-[130px]" title="openai/gpt-4o-mini">gpt-4o-mini</span>
          </div>
        </div>

        <!-- RAGLens Card -->
        <div class="rounded-lg border border-emerald-500/20 bg-emerald-950/10 p-3 space-y-2 text-xs">
          <div class="flex items-center justify-between">
            <span class="font-medium text-emerald-300 flex items-center gap-1.5">
              <i class="fa-solid fa-chart-line text-emerald-400"></i> RAGLens DevTools
            </span>
            <span class="px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-mono">RECORDING</span>
          </div>
          <p class="text-[11px] text-zinc-400 leading-snug">Every chat question streams real-time spans, tokens, and automated diagnostic evaluations into RAGLens.</p>
          <a id="raglens-dash-link" href="http://localhost:3000/projects/project_aaw3236s8tx5qsr1gi0wefnyj7/traces" target="_blank" class="inline-flex items-center gap-1.5 text-xs text-emerald-400 hover:text-emerald-300 font-medium transition-colors">
            Open Traces Explorer <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>
          </a>
        </div>
      </div>

      <!-- Controls -->
      <div class="space-y-4 pt-2 border-t border-zinc-800">
        <p class="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">RAG Retrieval Tuning</p>
        
        <div>
          <div class="flex justify-between text-xs mb-1">
            <span class="text-zinc-400">Top-K Candidates:</span>
            <span id="top-k-val" class="font-mono text-zinc-200">4</span>
          </div>
          <input id="top-k" type="range" min="1" max="8" value="4" class="w-full accent-emerald-500 cursor-pointer" oninput="document.getElementById('top-k-val').innerText = this.value" />
        </div>

        <div>
          <div class="flex justify-between text-xs mb-1">
            <span class="text-zinc-400">Min Score Threshold:</span>
            <span id="threshold-val" class="font-mono text-zinc-200">0.35</span>
          </div>
          <input id="threshold" type="range" min="0.10" max="0.80" step="0.05" value="0.35" class="w-full accent-emerald-500 cursor-pointer" oninput="document.getElementById('threshold-val').innerText = this.value" />
        </div>
      </div>

    </div>

    <!-- Clear / Reset -->
    <div class="p-4 border-t border-zinc-800 bg-zinc-950/40">
      <button onclick="clearChat()" class="w-full py-2 px-3 rounded-lg border border-zinc-800 hover:bg-zinc-800/80 text-xs text-zinc-400 hover:text-zinc-200 transition-colors flex items-center justify-center gap-2">
        <i class="fa-solid fa-trash-can text-[11px]"></i> Clear Conversation
      </button>
    </div>
  </aside>

  <!-- ── Main Chat Area ───────────────────────────────────────────────────── -->
  <main class="flex-1 flex flex-col bg-zinc-950 min-w-0">
    
    <!-- Top Header -->
    <header class="h-14 border-b border-zinc-800/80 px-6 flex items-center justify-between shrink-0 bg-zinc-900/20 backdrop-blur">
      <div class="flex items-center gap-3">
        <span class="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
        <span class="text-xs font-medium text-zinc-200">BookMyShow Customer Support Agent</span>
        <span class="text-xs text-zinc-500">•</span>
        <span class="text-xs text-zinc-400">Powered by Qdrant & OpenRouter</span>
      </div>
      <div class="flex items-center gap-3">
        <a href="http://localhost:3000/projects/project_aaw3236s8tx5qsr1gi0wefnyj7/traces" target="_blank" class="px-3 py-1.5 rounded-md bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-200 font-medium transition-colors flex items-center gap-1.5">
          <i class="fa-solid fa-chart-simple text-emerald-400"></i> RAGLens Dashboard
        </a>
      </div>
    </header>

    <!-- Chat Messages Container -->
    <div id="messages-container" class="flex-1 overflow-y-auto p-6 space-y-6">
      
      <!-- Hero / Welcome Greeting -->
      <div id="welcome-card" class="max-w-2xl mx-auto my-8 p-6 rounded-2xl border border-zinc-800/80 bg-gradient-to-b from-zinc-900/60 to-zinc-950/80 text-center space-y-4">
        <div class="h-12 w-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto text-xl shadow-inner">
          <i class="fa-solid fa-comments"></i>
        </div>
        <div>
          <h2 class="text-base font-semibold text-white">Ask anything about BookMyShow</h2>
          <p class="text-xs text-zinc-400 mt-1 max-w-md mx-auto">
            Test real dense vector search in Qdrant and real generation with OpenRouter. Every response links directly to its RAGLens trace.
          </p>
        </div>
        
        <!-- Suggested Questions -->
        <div class="grid grid-cols-2 gap-2 pt-2 text-left">
          <button onclick="fillQuery('Can I cancel my movie ticket and get a refund on BookMyShow?')" class="p-2.5 rounded-lg border border-zinc-800/80 bg-zinc-900/40 hover:bg-zinc-800/60 hover:border-zinc-700 text-xs text-zinc-300 transition-all">
            <span class="text-emerald-400 font-medium">🎟️ Cancellation:</span> How do ticket refunds work?
          </button>
          <button onclick="fillQuery('What is the difference between IMAX with Laser and 4DX seating?')" class="p-2.5 rounded-lg border border-zinc-800/80 bg-zinc-900/40 hover:bg-zinc-800/60 hover:border-zinc-700 text-xs text-zinc-300 transition-all">
            <span class="text-purple-400 font-medium">🎬 Cinema Tech:</span> IMAX Laser vs 4DX features
          </button>
          <button onclick="fillQuery('Are outside snacks or drinks permitted inside the auditorium?')" class="p-2.5 rounded-lg border border-zinc-800/80 bg-zinc-900/40 hover:bg-zinc-800/60 hover:border-zinc-700 text-xs text-zinc-300 transition-all">
            <span class="text-amber-400 font-medium">🍿 F&B Rules:</span> Outside food & pre-booking combos
          </button>
          <button onclick="fillQuery('How do I renew my driver license or passport?')" class="p-2.5 rounded-lg border border-zinc-800/80 bg-zinc-900/40 hover:bg-zinc-800/60 hover:border-zinc-700 text-xs text-zinc-300 transition-all">
            <span class="text-red-400 font-medium">⚠️ Out-of-Domain:</span> Test low retrieval confidence
          </button>
        </div>
      </div>

    </div>

    <!-- Input Bar -->
    <div class="p-4 border-t border-zinc-800/80 bg-zinc-900/30 shrink-0">
      <div class="max-w-4xl mx-auto">
        <form id="chat-form" onsubmit="handleSubmit(event)" class="relative flex items-center">
          <input
            id="query-input"
            type="text"
            placeholder="Ask about tickets, IMAX, cancellation, showtimes, or credit card offers..."
            autocomplete="off"
            class="w-full rounded-xl border border-zinc-700/80 bg-zinc-900/90 px-4 py-3.5 pr-28 text-sm text-zinc-100 placeholder-zinc-500 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 shadow-lg"
          />
          <button
            id="submit-btn"
            type="submit"
            class="absolute right-2 top-2 bottom-2 px-4 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span>Ask</span>
            <i class="fa-solid fa-paper-plane text-[10px]"></i>
          </button>
        </form>
        <p class="text-[11px] text-zinc-500 mt-2 text-center">
          Press <kbd class="px-1 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700">Enter</kbd> to submit. Live traces are ingested directly into RAGLens.
        </p>
      </div>
    </div>

  </main>

  <script>
    // Fetch initial status
    async function initStatus() {
      try {
        const res = await fetch('/api/status');
        const data = await res.json();
        document.getElementById('qdrant-mode-badge').innerText = data.qdrant.mode;
        document.getElementById('qdrant-count').innerText = data.qdrant.indexed_count;
        document.getElementById('qdrant-col').innerText = data.qdrant.collection;
        if (data.raglens.dashboard_url) {
          document.getElementById('raglens-dash-link').href = data.raglens.dashboard_url;
        }
      } catch (e) {
        console.error('Failed to load status:', e);
      }
    }
    initStatus();

    function fillQuery(text) {
      const input = document.getElementById('query-input');
      input.value = text;
      input.focus();
    }

    function clearChat() {
      const container = document.getElementById('messages-container');
      container.innerHTML = '';
      const welcome = document.createElement('div');
      welcome.id = 'welcome-card';
      welcome.className = 'max-w-2xl mx-auto my-8 p-6 rounded-2xl border border-zinc-800/80 bg-gradient-to-b from-zinc-900/60 to-zinc-950/80 text-center space-y-4';
      welcome.innerHTML = `
        <div class="h-12 w-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto text-xl shadow-inner">
          <i class="fa-solid fa-comments"></i>
        </div>
        <h2 class="text-base font-semibold text-white">Ask anything about BookMyShow</h2>
        <p class="text-xs text-zinc-400 mt-1 max-w-md mx-auto">Conversation cleared. Ready for your next query.</p>
      `;
      container.appendChild(welcome);
    }

    async function handleSubmit(e) {
      e.preventDefault();
      const input = document.getElementById('query-input');
      const btn = document.getElementById('submit-btn');
      const query = input.value.trim();
      if (!query) return;

      const welcome = document.getElementById('welcome-card');
      if (welcome) welcome.remove();

      input.value = '';
      input.disabled = true;
      btn.disabled = true;

      const container = document.getElementById('messages-container');

      // 1. Append User Message
      const userBubble = document.createElement('div');
      userBubble.className = 'flex justify-end';
      userBubble.innerHTML = `
        <div class="max-w-xl rounded-2xl rounded-tr-sm bg-zinc-800 border border-zinc-700/60 px-4 py-3 text-sm text-zinc-100 shadow-md">
          ${escapeHtml(query)}
        </div>
      `;
      container.appendChild(userBubble);
      container.scrollTop = container.scrollHeight;

      // 2. Append Loading Placeholder
      const loadingId = 'loading-' + Date.now();
      const loadingBubble = document.createElement('div');
      loadingBubble.id = loadingId;
      loadingBubble.className = 'flex items-start gap-3 max-w-3xl';
      loadingBubble.innerHTML = `
        <div class="h-8 w-8 rounded-lg bg-emerald-600/20 border border-emerald-500/30 text-emerald-400 flex items-center justify-center shrink-0 text-xs">
          <i class="fa-solid fa-robot"></i>
        </div>
        <div class="space-y-2 flex-1">
          <div class="flex items-center gap-2 text-xs text-zinc-400">
            <i class="fa-solid fa-circle-notch fa-spin text-emerald-400"></i>
            <span>Searching Qdrant & generating with OpenRouter...</span>
          </div>
        </div>
      `;
      container.appendChild(loadingBubble);
      container.scrollTop = container.scrollHeight;

      const top_k = parseInt(document.getElementById('top-k').value, 10);
      const threshold = parseFloat(document.getElementById('threshold').value);

      try {
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query, top_k, confidence_threshold: threshold })
        });

        if (!response.ok) {
          throw new Error('Server error: ' + response.statusText);
        }

        const data = await response.json();
        loadingBubble.remove();

        renderAssistantMessage(data);
      } catch (err) {
        loadingBubble.remove();
        const errBubble = document.createElement('div');
        errBubble.className = 'max-w-xl p-3 rounded-lg border border-red-500/30 bg-red-950/20 text-xs text-red-400 space-y-1';
        errBubble.innerHTML = `<strong>Error:</strong> ${err.message}`;
        container.appendChild(errBubble);
      } finally {
        input.disabled = false;
        btn.disabled = false;
        input.focus();
        container.scrollTop = container.scrollHeight;
      }
    }

    function renderAssistantMessage(data) {
      const container = document.getElementById('messages-container');
      const bubble = document.createElement('div');
      bubble.className = 'flex items-start gap-3 max-w-3xl';

      const traceId = data.trace_id || 'N/A';
      const traceUrl = data.trace_url || '#';
      const formattedAnswer = marked.parse(data.answer);

      // Score color helper
      function scoreBadge(score, selected) {
        if (!selected) return '<span class="px-1.5 py-0.5 rounded text-[10px] bg-zinc-800 text-zinc-500 border border-zinc-700">DISCARDED</span>';
        if (score >= 0.70) return `<span class="px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-mono">${(score).toFixed(4)}</span>`;
        if (score >= 0.45) return `<span class="px-1.5 py-0.5 rounded text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/30 font-mono">${(score).toFixed(4)}</span>`;
        return `<span class="px-1.5 py-0.5 rounded text-[10px] bg-red-500/10 text-red-400 border border-red-500/30 font-mono">${(score).toFixed(4)}</span>`;
      }

      // Build chunks accordion HTML
      let chunksHtml = '';
      if (data.retrieval && data.retrieval.length > 0) {
        chunksHtml = data.retrieval.map((c) => `
          <div class="border border-zinc-800/90 rounded-md p-2.5 bg-zinc-950/50 space-y-1 text-xs">
            <div class="flex items-center justify-between">
              <span class="font-medium text-zinc-200 truncate max-w-[280px]">[${c.rank}] ${escapeHtml(c.document_name)}</span>
              ${scoreBadge(c.score, c.selected)}
            </div>
            <p class="text-[11px] text-zinc-400 line-clamp-3 leading-relaxed">${escapeHtml(c.content)}</p>
          </div>
        `).join('');
      } else {
        chunksHtml = '<p class="text-xs text-zinc-500">No chunks retrieved.</p>';
      }

      bubble.innerHTML = `
        <div class="h-8 w-8 rounded-lg bg-emerald-600/20 border border-emerald-500/30 text-emerald-400 flex items-center justify-center shrink-0 text-xs">
          <i class="fa-solid fa-robot"></i>
        </div>
        <div class="space-y-3 flex-1 min-w-0">
          
          <!-- Answer Bubble -->
          <div class="rounded-2xl rounded-tl-sm bg-zinc-900 border border-zinc-800/80 p-4 text-sm text-zinc-200 shadow-sm leading-relaxed prose prose-invert max-w-none">
            ${formattedAnswer}
          </div>

          <!-- RAG Context & Telemetry Inspection Accordion -->
          <div class="rounded-xl border border-zinc-800 bg-zinc-900/40 p-3 space-y-2.5">
            
            <!-- Summary Bar -->
            <div class="flex flex-wrap items-center justify-between gap-2 text-xs">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 border border-zinc-700">
                  <i class="fa-solid fa-stopwatch text-[10px] text-zinc-400"></i> ${data.duration_ms} ms
                </span>
                <span class="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 border border-zinc-700">
                  <i class="fa-solid fa-coins text-[10px] text-amber-400"></i> ${data.metrics.total_tokens || 0} tokens
                </span>
                <span class="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 border border-zinc-700">
                  $${(data.metrics.estimated_cost || 0).toFixed(6)}
                </span>
              </div>

              <!-- RAGLens Link -->
              <a href="${traceUrl}" target="_blank" class="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-medium text-[11px] transition-colors">
                <i class="fa-solid fa-magnifying-glass-chart"></i> Inspect in RAGLens <i class="fa-solid fa-arrow-up-right-from-square text-[9px]"></i>
              </a>
            </div>

            <!-- Expandable Qdrant Chunks -->
            <details class="group pt-1 border-t border-zinc-800/60 text-xs">
              <summary class="cursor-pointer text-zinc-400 hover:text-zinc-200 select-none flex items-center justify-between py-1">
                <span class="font-medium flex items-center gap-1.5">
                  <i class="fa-solid fa-layer-group text-sky-400 text-[11px]"></i>
                  Qdrant Vector Retrieval (${data.retrieval ? data.retrieval.filter(r => r.selected).length : 0}/${data.retrieval ? data.retrieval.length : 0} chunks used)
                </span>
                <i class="fa-solid fa-chevron-down text-[10px] group-open:rotate-180 transition-transform"></i>
              </summary>
              <div class="mt-2 space-y-2 pl-1">
                ${chunksHtml}
              </div>
            </details>

          </div>

        </div>
      `;

      container.appendChild(bubble);
      container.scrollTop = container.scrollHeight;
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }
  </script>
</body>
</html>
"""


@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def index():
    return HTMLResponse(content=HTML_TEMPLATE)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8501, help="Port to serve the chat UI on (default: 8501)")
    parser.add_argument("--host", default="0.0.0.0", help="Host interface (default: 0.0.0.0)")
    args = parser.parse_args()

    print("\n" + "=" * 75)
    print("🌟 Starting BookMyShow RAGLens Chat Web Server")
    print(f"   👉 Open in your browser: http://localhost:{args.port}")
    print(f"   🔗 RAGLens Dashboard:   http://localhost:3000/projects/project_aaw3236s8tx5qsr1gi0wefnyj7/traces")
    print("=" * 75 + "\n")

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
