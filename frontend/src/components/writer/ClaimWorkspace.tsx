import { useEffect, useState } from "react";
import {
  getClaim,
  deleteManuscript,
  deleteSource,
  deleteClaim,
  isNetworkError,
  type ClaimDetail,
  type ManuscriptRead,
} from "../../api/writer";
import ManuscriptUpload from "./ManuscriptUpload";
import SourceUpload from "./SourceUpload";
import ConfirmDelete from "./ConfirmDelete";

export default function ClaimWorkspace({
  claimId,
  onBack,
  onDeleted,
}: {
  claimId: string;
  onBack: () => void;
  onDeleted: () => void;
}) {
  const [claim, setClaim] = useState<ClaimDetail | null>(null);
  const [error, setError] = useState(false);

  // local mirrors so uploads/deletes update the view without a refetch
  const [manuscript, setManuscript] = useState<ManuscriptRead | null>(null);
  const [sourcePaths, setSourcePaths] = useState<string[]>([]);

  useEffect(() => {
    void getClaim(claimId).then((res) => {
      if (isNetworkError(res)) {
        setError(true);
        return;
      }
      setClaim(res);
      setManuscript(res.manuscript);
      setSourcePaths(res.source_paths);
    });
  }, [claimId]);

  if (error) return <p className="text-sm text-caution">Couldn't load this claim.</p>;
  if (!claim) return <p className="text-sm text-muted">Loading…</p>;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <button onClick={onBack} className="mb-2 text-sm text-accent hover:underline">
            Back to claims
          </button>
          <h1 className="truncate font-mono text-lg text-ink">{claim.paper_ref}</h1>
        </div>
        <ConfirmDelete
          label="Delete claim"
          confirmLabel="Removes the manuscript and all source."
          onDelete={async () => {
            const res = await deleteClaim(claimId);
            if (res.ok) onDeleted();
            return res;
          }}
        />
      </div>

      <div className="flex flex-col gap-3">
        <ManuscriptUpload claimId={claimId} manuscript={manuscript} onChange={setManuscript} />
        {manuscript && (
          <div className="pl-1">
            <ConfirmDelete
              label="Delete manuscript"
              confirmLabel="Removes the stored manuscript text."
              onDelete={async () => {
                const res = await deleteManuscript(claimId);
                if (res.ok) setManuscript(null);
                return res;
              }}
            />
          </div>
        )}
      </div>

      <div className="flex flex-col gap-3">
        <SourceUpload claimId={claimId} sourcePaths={sourcePaths} onChange={setSourcePaths} />
        {sourcePaths.length > 0 && (
          <div className="pl-1">
            <ConfirmDelete
              label="Delete source"
              confirmLabel="Removes all stored source files."
              onDelete={async () => {
                const res = await deleteSource(claimId);
                if (res.ok) setSourcePaths([]);
                return res;
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
}
