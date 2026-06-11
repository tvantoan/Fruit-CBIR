import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { getOptimizationStatus, startOptimization, evaluateFeatures, evaluateTestDataset } from '../services/api'

const weightLabels = {
  color: 'Color',
  color_moments: 'Color Moments',
  texture: 'Texture (LBP)',
  glcm: 'GLCM',
  shape: 'Shape',
}

function WeightRow({ label, value }) {
  return (
    <div className="flex justify-between text-sm text-gray-700 py-1 border-b border-gray-100">
      <span>{label}</span>
      <span className="font-medium">{value != null ? value.toFixed(3) : '-'}</span>
    </div>
  )
}

function AdminPage() {
  const [status, setStatus] = useState(null)
  const [nTrials, setNTrials] = useState(100)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const pollRef = useRef(null)

  // Feature evaluation state
  const [featureMAPs, setFeatureMAPs] = useState(null)
  const [subsetSize, setSubsetSize] = useState(100)
  const [evaluating, setEvaluating] = useState(false)
  const [evalError, setEvalError] = useState(null)
  const [testMetrics, setTestMetrics] = useState(null)
  const [testSamples, setTestSamples] = useState(null)
  const [testSampleSize, setTestSampleSize] = useState(50)
  const [testTopK, setTestTopK] = useState(5)
  const [evaluatingTest, setEvaluatingTest] = useState(false)
  const [testError, setTestError] = useState(null)

  const progress = useMemo(() => {
    if (!status || !status.total_trials) return 0
    return Math.round((status.current_trial / status.total_trials) * 100)
  }, [status])

  const fetchStatus = async () => {
    try {
      const data = await getOptimizationStatus()
      setStatus(data)
      setError(null)
    } catch (_err) {
      setError('Không thể lấy trạng thái tối ưu hóa')
    }
  }

  const handleStart = async () => {
    if (nTrials <= 0) {
      setError('Số trials phải lớn hơn 0')
      return
    }
    setLoading(true)
    setError(null)
    try {
      await startOptimization({ nTrials })
      await fetchStatus()
    } catch (_err) {
      setError('Không thể khởi động tối ưu hóa. Xin thử lại.')
    } finally {
      setLoading(false)
    }
  }

  const handleEvaluate = async () => {
    if (subsetSize <= 0) {
      setEvalError('Subset size phải lớn hơn 0')
      return
    }
    setEvaluating(true)
    setEvalError(null)
    try {
      const data = await evaluateFeatures({ subsetSize })
      setFeatureMAPs(data.feature_mAPs)
    } catch (_err) {
      setEvalError('Không thể đánh giá features. Xin thử lại.')
    } finally {
      setEvaluating(false)
    }
  }

  const handleEvaluateTestDataset = async () => {
    if (testSampleSize <= 0 || testTopK <= 1) {
      setTestError('Sample size phải > 0 và topK phải >= 1')
      return
    }
    setEvaluatingTest(true)
    setTestError(null)
    try {
      const data = await evaluateTestDataset({ sampleSize: testSampleSize, topK: testTopK })
      setTestMetrics({
        top_k: data.top_k,
        global: data.global_metrics,
        per_fruit: data.per_fruit_metrics,
        confusion_matrix: data.confusion_matrix,
      })
      setTestSamples(data.sample_results)
    } catch (_err) {
      setTestError('Không thể đánh giá test dataset. Xin thử lại.')
    } finally {
      setEvaluatingTest(false)
    }
  }

  useEffect(() => {
    fetchStatus()
  }, [])

  useEffect(() => {
    if (!status || status.status !== 'running') {
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
      return
    }

    if (!pollRef.current) {
      pollRef.current = setInterval(fetchStatus, 2000)
    }

    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
    }
  }, [status])

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Admin Optimization</h1>
          <p className="text-gray-500">Theo dõi tiến trình tối ưu hóa trọng số feature trên dataset.</p>
        </div>
        <Link to="/" className="text-sm text-green-600 hover:underline">
          &larr; Back to Home
        </Link>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.3fr_0.9fr]">
        <section className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-800">Optimization Control</h2>
              <p className="text-sm text-gray-500">Bắt đầu chạy Optuna để tìm bộ trọng số tốt nhất.</p>
            </div>
            <button
              type="button"
              onClick={handleStart}
              disabled={loading || (status && status.status === 'running')}
              className="inline-flex items-center justify-center rounded-xl bg-green-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-green-700 disabled:cursor-not-allowed disabled:bg-gray-300"
            >
              {status?.status === 'running' ? 'Running...' : 'Start Optimization'}
            </button>
          </div>

          <div className="rounded-2xl border border-gray-200 bg-gray-50 p-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Number of Trials
            </label>
            <input
              type="number"
              value={nTrials}
              onChange={(e) => setNTrials(Math.max(1, parseInt(e.target.value) || 1))}
              disabled={status && status.status === 'running'}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm disabled:bg-gray-200 disabled:cursor-not-allowed"
              min="1"
              max="1000"
            />
          </div>

          <div className="rounded-2xl border border-gray-200 bg-gray-50 p-4">
            <div className="flex items-center justify-between text-sm text-gray-500 mb-3">
              <span>Status</span>
              <span className="font-semibold text-gray-700">{status?.status || 'idle'}</span>
            </div>
            <div className="w-full rounded-full bg-white h-3 overflow-hidden border border-gray-200">
              <div
                className="h-full bg-green-500 transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className="mt-3 text-sm text-gray-600">
              {status?.current_trial != null && status?.total_trials ? (
                <span>{status.current_trial} / {status.total_trials} trials</span>
              ) : (
                <span>Chưa có tiến trình nào được ghi nhận.</span>
              )}
            </div>
          </div>

          {error && (
            <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl border border-gray-200 bg-white p-4">
              <h3 className="text-sm font-semibold text-gray-800 mb-3">Current trial</h3>
              <WeightRow label="Best mAP so far" value={status?.best_mAP ?? null} />
              {Object.entries(status?.last_trial_weights || {}).map(([key, value]) => (
                <WeightRow key={key} label={weightLabels[key] || key} value={value} />
              ))}
            </div>

            <div className="rounded-2xl border border-gray-200 bg-white p-4">
              <h3 className="text-sm font-semibold text-gray-800 mb-3">Best weights</h3>
              {Object.entries(status?.best_weights || {}).map(([key, value]) => (
                <WeightRow key={key} label={weightLabels[key] || key} value={value} />
              ))}
            </div>
          </div>
        </section>

        <section className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-800">Feature Evaluation</h2>
              <p className="text-sm text-gray-500">Đánh giá mAP cho từng feature riêng lẻ trên subset của dataset.</p>
            </div>
            <button
              type="button"
              onClick={handleEvaluate}
              disabled={evaluating}
              className="inline-flex items-center justify-center rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-300"
            >
              {evaluating ? 'Evaluating...' : 'Evaluate Features'}
            </button>
          </div>

          <div className="rounded-2xl border border-gray-200 bg-gray-50 p-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Subset Size
            </label>
            <input
              type="number"
              value={subsetSize}
              onChange={(e) => setSubsetSize(Math.max(1, parseInt(e.target.value) || 1))}
              disabled={evaluating}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm disabled:bg-gray-200 disabled:cursor-not-allowed"
              min="1"
              max="1000"
            />
          </div>

          {evalError && (
            <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {evalError}
            </div>
          )}

          {featureMAPs && (
            <div className="rounded-2xl border border-gray-200 bg-white p-4">
              <h3 className="text-sm font-semibold text-gray-800 mb-3">Feature mAP Scores</h3>
              {Object.entries(featureMAPs).map(([feature, mAP]) => (
                <WeightRow key={feature} label={weightLabels[feature] || feature} value={mAP} />
              ))}
            </div>
          )}
        </section>
      </div>

      <section className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-800">Test Dataset Evaluation</h2>
            <p className="text-sm text-gray-500">Chạy các test queries trên tập test và trả về chỉ số top-1/top-5.</p>
          </div>
          <button
            type="button"
            onClick={handleEvaluateTestDataset}
            disabled={evaluatingTest}
            className="inline-flex items-center justify-center rounded-xl bg-indigo-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-gray-300"
          >
            {evaluatingTest ? 'Evaluating...' : 'Evaluate Test Dataset'}
          </button>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="rounded-2xl border border-gray-200 bg-gray-50 p-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Sample Size</label>
            <input
              type="number"
              value={testSampleSize}
              onChange={(e) => setTestSampleSize(Math.max(1, parseInt(e.target.value) || 1))}
              disabled={evaluatingTest}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm disabled:bg-gray-200 disabled:cursor-not-allowed"
              min="1"
              max="500"
            />
          </div>
          <div className="rounded-2xl border border-gray-200 bg-gray-50 p-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Top K</label>
            <input
              type="number"
              value={testTopK}
              onChange={(e) => setTestTopK(Math.max(1, parseInt(e.target.value) || 1))}
              disabled={evaluatingTest}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm disabled:bg-gray-200 disabled:cursor-not-allowed"
              min="1"
              max="20"
            />
          </div>
        </div>

        {testError && (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {testError}
          </div>
        )}

        {testMetrics && (
          <div className="rounded-2xl border border-gray-200 bg-white p-4 space-y-6">
            {/* Global Metrics */}
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-gray-800">Global Metrics (top-{testMetrics.top_k})</h3>
              <div className="grid gap-4 sm:grid-cols-3">
                <div className="rounded-xl border border-gray-200 bg-gray-50 p-3">
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Top-1 Accuracy</div>
                  <div className="text-2xl font-bold text-green-600">{(testMetrics.global.mean_top1_accuracy * 100).toFixed(2)}%</div>
                </div>
                <div className="rounded-xl border border-gray-200 bg-gray-50 p-3">
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Top-{testMetrics.top_k} Accuracy</div>
                  <div className="text-2xl font-bold text-blue-600">{(testMetrics.global.mean_topk_accuracy * 100).toFixed(2)}%</div>
                </div>
                <div className="rounded-xl border border-gray-200 bg-gray-50 p-3">
                  <div className="text-xs text-gray-500 uppercase tracking-wide">mAP@{testMetrics.top_k}</div>
                  <div className="text-2xl font-bold text-purple-600">{testMetrics.global.mAP_at_k.toFixed(4)}</div>
                </div>
              </div>
              <div className="grid gap-4 sm:grid-cols-4">
                <div className="rounded-xl border border-gray-200 bg-gray-50 p-3">
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Precision@{testMetrics.top_k}</div>
                  <div className="text-xl font-bold text-orange-600">{testMetrics.global.mean_precision_at_k.toFixed(4)}</div>
                </div>
                <div className="rounded-xl border border-gray-200 bg-gray-50 p-3">
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Recall@{testMetrics.top_k}</div>
                  <div className="text-xl font-bold text-red-600">{testMetrics.global.mean_recall_at_k.toFixed(4)}</div>
                </div>
                <div className="rounded-xl border border-gray-200 bg-gray-50 p-3">
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Mean F1</div>
                  <div className="text-xl font-bold text-pink-600">{testMetrics.global.mean_f1.toFixed(4)}</div>
                </div>
                <div className="rounded-xl border border-gray-200 bg-gray-50 p-3">
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Mean Search Time</div>
                  <div className="text-xl font-bold text-indigo-600">{testMetrics.global.mean_search_time_ms.toFixed(2)}ms</div>
                </div>
              </div>
              <p className="text-xs text-gray-500">
                Precision@k = trung bình tỉ lệ kết quả đúng trong top-k mỗi query. Recall@k = đúng/tổng ảnh cùng loại trong DB. mAP@k đánh giá thứ tự.
              </p>
            </div>

            {/* Per-Fruit Metrics */}
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-gray-800">Per-Fruit Breakdown</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm border-collapse">
                  <thead>
                    <tr className="border-b border-gray-200 bg-gray-50">
                      <th className="px-3 py-2 text-left font-semibold text-gray-700">Fruit</th>
                      <th className="px-3 py-2 text-right font-semibold text-gray-700">Queries</th>
                      <th className="px-3 py-2 text-right font-semibold text-gray-700">Top-1</th>
                      <th className="px-3 py-2 text-right font-semibold text-gray-700">Top-{testMetrics.top_k}</th>
                      <th className="px-3 py-2 text-right font-semibold text-gray-700">P@{testMetrics.top_k}</th>
                      <th className="px-3 py-2 text-right font-semibold text-gray-700">R@{testMetrics.top_k}</th>
                      <th className="px-3 py-2 text-right font-semibold text-gray-700">F1</th>
                      <th className="px-3 py-2 text-right font-semibold text-gray-700">mAP@{testMetrics.top_k}</th>
                      <th className="px-3 py-2 text-right font-semibold text-gray-700">Avg Time (ms)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(testMetrics.per_fruit || {}).map(([fruit, metrics]) => (
                      <tr key={fruit} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="px-3 py-2 text-left font-medium text-gray-700">{fruit}</td>
                        <td className="px-3 py-2 text-right text-gray-600">{metrics.queries_count}</td>
                        <td className="px-3 py-2 text-right"><span className="inline-block rounded-full bg-green-100 px-2 py-1 text-green-700">{(metrics.top1_accuracy * 100).toFixed(1)}%</span></td>
                        <td className="px-3 py-2 text-right"><span className="inline-block rounded-full bg-blue-100 px-2 py-1 text-blue-700">{(metrics.topk_accuracy * 100).toFixed(1)}%</span></td>
                        <td className="px-3 py-2 text-right text-orange-600 font-medium">{metrics.precision_at_k.toFixed(3)}</td>
                        <td className="px-3 py-2 text-right text-red-600 font-medium">{metrics.recall_at_k.toFixed(3)}</td>
                        <td className="px-3 py-2 text-right text-pink-600 font-medium">{metrics.f1.toFixed(3)}</td>
                        <td className="px-3 py-2 text-right text-purple-600 font-medium">{metrics.mAP_at_k.toFixed(3)}</td>
                        <td className="px-3 py-2 text-right text-indigo-600 font-medium">{metrics.mean_search_time_ms.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Confusion Matrix */}
            {testMetrics.confusion_matrix && (
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-gray-800">
                  Confusion Matrix (top-{testMetrics.top_k})
                </h3>
                <p className="text-xs text-gray-500">
                  Hàng = nhãn thật của query. Cột = nhãn được trả về. Mỗi cell = % slot trong top-{testMetrics.top_k} là nhãn cột (mỗi hàng cộng lại = 100%).
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm border-collapse">
                    <thead>
                      <tr className="bg-gray-50">
                        <th className="px-3 py-2 text-left font-semibold text-gray-700 border border-gray-200">
                          Actual \ Predicted
                        </th>
                        {testMetrics.confusion_matrix.labels.map((label) => (
                          <th
                            key={label}
                            className="px-3 py-2 text-center font-semibold text-gray-700 border border-gray-200"
                          >
                            {label}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {testMetrics.confusion_matrix.rows.map((row) => (
                        <tr key={row.true_label}>
                          <td className="px-3 py-2 text-left font-semibold text-gray-700 border border-gray-200 bg-gray-50">
                            {row.true_label}
                            <span className="block text-xs font-normal text-gray-400">
                              ({row.queries_count} queries)
                            </span>
                          </td>
                          {testMetrics.confusion_matrix.labels.map((pred_label) => {
                            const cell = row.cells[pred_label] || { count: 0, percent: 0 }
                            const isDiag = row.true_label === pred_label
                            const intensity = Math.min(1, cell.percent)
                            const bg = isDiag
                              ? `rgba(34, 197, 94, ${0.15 + intensity * 0.55})`
                              : `rgba(239, 68, 68, ${intensity * 0.5})`
                            return (
                              <td
                                key={pred_label}
                                className="px-3 py-2 text-center border border-gray-200"
                                style={{ backgroundColor: bg }}
                                title={`${cell.count} kết quả`}
                              >
                                <div className="font-semibold text-gray-800">
                                  {(cell.percent * 100).toFixed(1)}%
                                </div>
                                <div className="text-xs text-gray-500">{cell.count}</div>
                              </td>
                            )
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            <div className="rounded-2xl border border-gray-200 bg-gray-50 p-4">
              <h3 className="text-sm font-semibold text-gray-800 mb-3">Sample Results</h3>
              {testSamples?.map((sample) => (
                <div key={sample.query_file} className="mb-4">
                  <div className="text-sm font-medium text-gray-700">Query: {sample.query_file}</div>
                  <div className="text-sm text-gray-500 mb-2">Label: {sample.label}</div>
                  <div className="space-y-2">
                    {sample.top_results.map((result, index) => (
                      <div key={index} className="rounded-2xl border border-gray-200 bg-white p-3 text-sm">
                        <div className="font-semibold text-gray-700">{index + 1}. {result.fruit_name}</div>
                        <div className="text-gray-500">File: {result.filename}</div>
                        <div className="text-gray-500">Similarity: {result.similarity}</div>
                        <div className="text-gray-500">Distance: {result.distance}</div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>
    </div>
  )
}

export default AdminPage
