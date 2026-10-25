import { type Ref, computed } from "vue";
import MarkdownIt from "markdown-it";
import DOMPurify from "dompurify";

const md = new MarkdownIt({ html: false, linkify: true, typographer: true });

export function useSafeMarkdown(source: Ref<string> | (() => string)) {
  return computed(() => {
    const raw = typeof source === "function" ? source() : source.value;
    if (!raw) return "";
    const rendered = md.render(raw);
    return DOMPurify.sanitize(rendered);
  });
}
