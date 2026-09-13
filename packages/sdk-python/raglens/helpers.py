"""Log structured data into existing spans so timing includes the actual work."""


def log_retrieval(span, results, method="cosine", query=None):
    span.retrieval_results = [dict(result, rank=result.get("rank", i),
                                   retrieval_method=result.get("retrieval_method", method))
                              for i, result in enumerate(results, 1)]
    span.set_attributes({"retrieval_method": method, "top_k": len(results)})
    if query is not None:
        span.input = {"query": query}
    span.set_output({"results": span.retrieval_results})


def log_context(span, context, tokens, max_tokens=None, chunks=None):
    span.set_output({"context": context, "chunks": chunks or []})
    span.set_attributes({"token_count": tokens, "max_tokens": max_tokens})
    span.trace.metrics["context_tokens"] = span.trace.metrics.get("context_tokens", 0) + tokens


def log_prompt(span, prompt, tokens=None, template_variables=None):
    span.set_output({"messages" if isinstance(prompt, list) else "prompt": prompt})
    span.set_attributes({"token_count": tokens, "template_variables": template_variables or {}})


def log_generation(span, response, tokens, model, provider="mock", **attributes):
    usage = {"input_tokens": tokens, "output_tokens": 0} if isinstance(tokens, int) else dict(tokens)
    span.set_output({"content": response})
    span.set_attributes({"model": model, "provider": provider, **usage, **attributes})
    for key in ("input_tokens", "output_tokens"):
        span.trace.metrics[key] = span.trace.metrics.get(key, 0) + usage.get(key, 0)
    span.trace.metrics["total_tokens"] = (span.trace.metrics.get("input_tokens", 0) +
                                           span.trace.metrics.get("output_tokens", 0))
