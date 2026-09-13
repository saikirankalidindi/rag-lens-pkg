import Link from "next/link";
import { CodeBlock } from "../../components/docs/CodeBlock";

const minimal = `from raglens import RAGLens

raglens = RAGLens()  # RAGLENS_API_KEY + RAGLENS_BASE_URL
with raglens.trace("answer_question", input={"query": "What is RAG?"}) as trace:
    trace.set_output({"answer": "Retrieval augmented generation."})

print(trace.id)   # persisted ID
print(trace.url)  # dashboard URL when project_id is configured`;

const complete = `from raglens import RAGLens, log_retrieval, log_context
from raglens import log_prompt, log_generation

with RAGLens().trace("customer_support_rag", input={"query": question}) as trace:
    with trace.span("query", "normalize_query") as span:
        normalized = question.strip()
        span.set_output({"normalized_query": normalized})

    with trace.span("retrieval", "vector_search") as span:
        results = [{
            "chunk_id": "orders-12", "document_id": "orders",
            "document_name": "Order policy",
            "content": "Orders can be cancelled within 30 days.",
            "score": 0.91, "selected": True,
        }]
        log_retrieval(span, results, method="qdrant_cosine", query=normalized)

    context = results[0]["content"]
    with trace.span("context", "assemble_context") as span:
        log_context(span, context, tokens=8, max_tokens=4096,
                    chunks=[{"content": context, "source": "Order policy"}])

    messages = [{"role": "system", "content": "Answer only from context."},
                {"role": "user", "content": context}]
    with trace.span("prompt", "render_prompt") as span:
        log_prompt(span, messages, tokens=18,
                   template_variables={"query": normalized})

    with trace.span("llm", "generate_answer") as span:
        answer = "Orders can be cancelled within 30 days."
        log_generation(span, answer,
                       tokens={"input_tokens": 18, "output_tokens": 9},
                       model="your-model", provider="your-provider")
    trace.set_output({"answer": answer})`;

const failure = `try:
    with raglens.trace("failed_request") as trace:
        with trace.span("retrieval", "qdrant_search"):
            raise TimeoutError("vector database timed out")
except TimeoutError:
    print("Application handled the timeout")

print(trace.status)            # error
print(trace.spans[-1].status)  # error`;

function Section({ id, eyebrow, title, children }: { id: string; eyebrow: string; title: string; children: React.ReactNode }) {
  return <section id={id} className="scroll-mt-24 space-y-5"><div><p className="mb-2 text-xs font-medium uppercase tracking-[.16em] text-cyan-300">{eyebrow}</p><h2 className="text-2xl font-semibold tracking-tight">{title}</h2></div>{children}</section>;
}

export default function DocsPage() {
  return <main className="min-h-screen bg-[#0b0d11] text-zinc-100">
    <header className="sticky top-0 z-10 border-b border-white/[0.07] bg-[#0b0d11]/90 px-5 backdrop-blur lg:px-10"><div className="mx-auto flex h-16 max-w-7xl items-center justify-between"><Link href="/projects" className="text-sm font-semibold">RAGLens <span className="font-normal text-zinc-500">/ Developer quickstart</span></Link><div className="flex gap-4 text-xs"><Link href="/projects" className="text-zinc-400 hover:text-white">Back to projects</Link><a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" className="text-zinc-400 hover:text-white">API reference ↗</a></div></div></header>
    <div className="mx-auto grid max-w-7xl gap-10 px-5 py-10 lg:grid-cols-[220px_minmax(0,760px)] lg:px-10"><aside className="hidden lg:block"><nav className="sticky top-24 space-y-1 text-xs text-zinc-500"><p className="mb-4 px-3 text-[10px] uppercase tracking-[.18em]">On this page</p>{[["setup","Setup"],["first-trace","First trace"],["full-rag","Full RAG trace"],["helpers","Helper methods"],["failures","Failures & disabled mode"],["demos","Run the demos"],["troubleshooting","Troubleshooting"]].map(([id,label]) => <a key={id} href={`#${id}`} className="block rounded px-3 py-2 hover:bg-white/5 hover:text-white">{label}</a>)}</nav></aside>
      <article className="min-w-0 space-y-14"><section><p className="mb-4 text-xs font-medium uppercase tracking-[.16em] text-cyan-300">Developer quickstart</p><h1 className="max-w-3xl text-4xl font-semibold tracking-tight sm:text-5xl">Instrument your RAG pipeline<span className="text-cyan-300">.</span></h1><p className="mt-5 max-w-2xl text-base leading-7 text-zinc-400">Capture what your application retrieved, assembled, prompted, and generated. These examples work with any retriever and model provider.</p><div className="mt-7 flex flex-wrap gap-3"><Link href="#setup" className="rounded-lg bg-cyan-300 px-4 py-2.5 text-sm font-medium text-zinc-950 hover:bg-cyan-200">Start setup →</Link><Link href="#full-rag" className="rounded-lg border border-white/10 px-4 py-2.5 text-sm text-zinc-300 hover:bg-white/5">See full example</Link></div></section>
        <Section id="setup" eyebrow="01 · Setup" title="Start the stack and create a project"><div className="space-y-6"><Step number="1" title="Start RAGLens"><CodeBlock code={`cp .env.example .env\ndocker compose up --build`} label="Terminal" /></Step><Step number="2" title="Create an ingestion key"><p className="text-sm leading-6 text-zinc-400">Open <a className="text-cyan-300 underline" href="http://localhost:3000">localhost:3000</a>, register, create a project, and open <strong className="text-zinc-200">Settings → API Keys</strong>. Copy the key before closing the dialog; it is shown once.</p></Step><Step number="3" title="Install and configure the SDK"><CodeBlock code={`python -m venv .venv\nsource .venv/bin/activate\npython -m pip install -e packages/sdk-python\n\nexport RAGLENS_API_KEY='rgl_test_replace_with_your_key'\nexport RAGLENS_PROJECT_ID='project_replace_with_your_project_id'\nexport RAGLENS_BASE_URL='http://localhost:8000'`} label="Terminal" /></Step></div></Section>
        <Section id="first-trace" eyebrow="02 · First trace" title="Send the smallest useful trace"><p className="text-sm leading-6 text-zinc-400">Save this as <code className="rounded bg-white/10 px-1.5 py-0.5 text-zinc-200">quick_trace.py</code>. The SDK sends the trace when the <code className="rounded bg-white/10 px-1.5 py-0.5 text-zinc-200">with</code> block exits.</p><CodeBlock code={minimal} /><Info>UTC timestamps and duration are captured automatically. Set <code>project_id</code> on <code>RAGLens</code> to populate a direct dashboard URL.</Info></Section>
        <Section id="full-rag" eyebrow="03 · Full RAG trace" title="Give every pipeline stage a span"><p className="text-sm leading-6 text-zinc-400">Explicit spans make the waterfall useful. Nested spans automatically receive <code>parent_span_id</code>.</p><CodeBlock code={complete} /><Info>Retrieval cards show rank, score, document, content, and selection. Context and prompt inspectors show tokens and sources. The LLM inspector shows model, provider, usage, latency, and attributes.</Info></Section>
        <Section id="helpers" eyebrow="04 · Helper methods" title="Log structured data quickly"><p className="text-sm leading-6 text-zinc-400">Trace-level helpers create a short span and return it. Use an explicit span when you need the operation&apos;s actual latency.</p><CodeBlock code={`with raglens.trace("helper_example") as trace:\n    trace.log_retrieval(results=[{\n        "chunk_id": "c1", "document_id": "d1",\n        "document_name": "FAQ", "content": "The answer is here.",\n        "score": 0.88, "selected": True,\n    }], method="bm25", query="Where is the answer?")\n    trace.log_context(context="The answer is here.", tokens=5, max_tokens=2048)\n    trace.log_prompt(prompt="Answer from context", tokens=5)\n    trace.log_generation(response="The answer is here.",\n                         tokens={"input_tokens": 5, "output_tokens": 4},\n                         model="mock-model")`} /><div className="overflow-x-auto rounded-xl border border-white/[0.07]"><table className="w-full min-w-[560px] text-left text-xs"><thead className="border-b border-white/[0.07] bg-white/[0.03] text-zinc-400"><tr><th className="px-4 py-3">Helper</th><th className="px-4 py-3">Records</th><th className="px-4 py-3">Useful fields</th></tr></thead><tbody className="divide-y divide-white/[0.06] text-zinc-300"><tr><td className="px-4 py-3 font-mono text-cyan-200">log_retrieval</td><td className="px-4 py-3">Candidate chunks</td><td className="px-4 py-3 text-zinc-500">score, rank, selected, source</td></tr><tr><td className="px-4 py-3 font-mono text-cyan-200">log_context</td><td className="px-4 py-3">Assembled context</td><td className="px-4 py-3 text-zinc-500">tokens, max_tokens, chunks</td></tr><tr><td className="px-4 py-3 font-mono text-cyan-200">log_prompt</td><td className="px-4 py-3">Prompt/messages</td><td className="px-4 py-3 text-zinc-500">tokens, template_variables</td></tr><tr><td className="px-4 py-3 font-mono text-cyan-200">log_generation</td><td className="px-4 py-3">Model response</td><td className="px-4 py-3 text-zinc-500">model, provider, input/output tokens</td></tr></tbody></table></div></Section>
        <Section id="failures" eyebrow="05 · Reliability" title="Errors are recorded without taking down your app"><p className="text-sm leading-6 text-zinc-400">The exception continues through your normal application handler while the trace and failed span are marked as errors.</p><CodeBlock code={failure} /><div className="grid gap-3 sm:grid-cols-2"><Info title="Disable tracing">Set <code>RAGLENS_ENABLED=false</code> for local runs or an emergency switch. No request is sent.</Info><Info title="Delivery failures">Missing keys, network errors, HTTP errors, and malformed responses produce a warning. The default timeout is two seconds and delivery is not retried.</Info></div></Section>
        <Section id="demos" eyebrow="06 · Demos" title="Run a complete example"><div className="grid gap-4 sm:grid-cols-2"><Demo title="Offline basic RAG" text="Local TF-IDF retrieval and mock generation. No API keys required." code={`python -m pip install -r examples/basic-rag/requirements.txt\npython examples/basic-rag/app.py --offline`} /><Demo title="Qdrant + OpenRouter" text="Real embeddings, vector search, generation, and telemetry. Configure the example .env first." code={`cp examples/qdrant-openrouter-rag/.env.example examples/qdrant-openrouter-rag/.env\npython examples/qdrant-openrouter-rag/app.py --demo\npython examples/qdrant-openrouter-rag/chat_server.py --port 8501`} /></div></Section>
        <Section id="troubleshooting" eyebrow="07 · Troubleshooting" title="When a trace does not appear"><div className="space-y-3 rounded-xl border border-white/[0.08] bg-white/[0.02] p-5 text-sm leading-6 text-zinc-400"><p><strong className="text-zinc-200">Check the key.</strong> It must be active and belong to the project you are viewing.</p><p><strong className="text-zinc-200">Check the URL.</strong> The local API is normally <code>http://localhost:8000</code>.</p><p><strong className="text-zinc-200">Check the switch.</strong> <code>RAGLENS_ENABLED</code> must not be false.</p><p><strong className="text-zinc-200">Rebuild Docker.</strong> Run <code>docker compose up -d --build api web</code> after dependency or frontend changes.</p></div><div className="flex flex-wrap items-center justify-between gap-3 border-t border-white/[0.07] pt-6 text-xs text-zinc-500"><span>Need the complete reference?</span><Link href="https://github.com/your-org/raglens/blob/main/docs/QUICKSTART.md" target="_blank" className="text-cyan-300 hover:text-cyan-200">Open full quick start ↗</Link></div></Section>
      </article></div>
  </main>;
}

function Step({ number, title, children }: { number: string; title: string; children: React.ReactNode }) { return <div className="flex gap-4"><span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-cyan-300/20 bg-cyan-300/10 text-xs text-cyan-300">{number}</span><div className="min-w-0 flex-1"><p className="mb-2 text-sm font-medium">{title}</p>{children}</div></div>; }
function Info({ title, children }: { title?: string; children: React.ReactNode }) { return <div className="rounded-xl border border-cyan-300/15 bg-cyan-300/[0.04] p-4 text-sm leading-6 text-zinc-400">{title && <p className="mb-1 font-medium text-cyan-200">{title}</p>}{children}</div>; }
function Demo({ title, text, code }: { title: string; text: string; code: string }) { return <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-5"><h3 className="font-medium">{title}</h3><p className="my-2 text-xs leading-5 text-zinc-500">{text}</p><CodeBlock code={code} label="Terminal" /></div>; }
