import { useEffect, useState } from "react";
import type { Entry, SourceSummary } from "./types";
import { catalog, loadNarratives } from "./archive";
export default function EventNarrative({ entry }: { entry: Entry }) {
  const [accounts, setAccounts] = useState<SourceSummary[]>([]);
  const [error, setError] = useState(false);
  useEffect(() => {
    let cancelled = false;
    setAccounts([]);
    setError(false);
    const sourceIds = [...new Set(entry.citations.map((c) => c.sourceId))];
    Promise.all(sourceIds.map(loadNarratives))
      .then(
        (books) =>
          !cancelled &&
          setAccounts(books.flatMap((book) => book[entry.id] || [])),
      )
      .catch(() => !cancelled && setError(true));
    return () => {
      cancelled = true;
    };
  }, [entry]);
  return (
    <div className="event-narrative">
      <h4>What the source says</h4>
      {!accounts.length && (
        <p role="status">
          {error
            ? "Could not load the detailed source account. Reload to try again."
            : "Opening the source account…"}
        </p>
      )}
      {accounts.map((account) => (
        <article key={account.sourceId}>
          <span className="tiny-label">
            {catalog.sources.find((s) => s.id === account.sourceId)?.author ||
              "Bruce Porter Roberts"}{" "}
            · {catalog.sources.find((s) => s.id === account.sourceId)?.title}
          </span>
          {account.details.map((paragraph, i) => (
            <p key={i}>{paragraph}</p>
          ))}
          <h4>Why this point connects the threads</h4>
          <p className="event-context">{account.context}</p>
          {account.precisionNote && (
            <p className="event-date-note">
              <b>Date note.</b> {account.precisionNote}
            </p>
          )}
        </article>
      ))}
    </div>
  );
}
