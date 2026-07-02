export default function FeatureImportance() {
  return (
    <div className="space-y-2">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
        Feature Importance
      </h2>
      <img
        src="/api/importance"
        alt="Feature Importance chart"
        className="w-full rounded-lg"
        onError={e => { e.target.style.display = 'none' }}
      />
    </div>
  )
}
