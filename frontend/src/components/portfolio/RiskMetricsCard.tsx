import { RiskMetrics } from '@/types'
import { 
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'
import { clsx } from 'clsx'

interface RiskMetricsCardProps {
  metrics: RiskMetrics
}

export const RiskMetricsCard = ({ metrics }: RiskMetricsCardProps) => {
  const getDrawdownColor = (drawdown: number) => {
    if (drawdown < 5) return 'text-green-400'
    if (drawdown < 10) return 'text-yellow-400'
    return 'text-red-400'
  }

  const getSharpeColor = (sharpe: number) => {
    if (sharpe > 2) return 'text-green-400'
    if (sharpe > 1) return 'text-yellow-400'
    return 'text-red-400'
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h3 className="text-xl font-bold mb-6">Risk Analytics</h3>
      
      <div className="grid grid-cols-2 gap-6">
        {/* Value at Risk */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <ExclamationTriangleIcon className="h-5 w-5 text-orange-400" />
            <span className="text-sm font-medium text-gray-400">Value at Risk (95%)</span>
          </div>
          <p className="text-2xl font-bold text-orange-400">
            ${metrics.value_at_risk.toFixed(2)}
          </p>
          <p className="text-xs text-gray-500">
            Maximum expected loss in 95% of cases
          </p>
        </div>

        {/* Sharpe Ratio */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <ArrowTrendingUpIcon className="h-5 w-5 text-blue-400" />
            <span className="text-sm font-medium text-gray-400">Sharpe Ratio</span>
          </div>
          <p className={clsx('text-2xl font-bold', getSharpeColor(metrics.sharpe_ratio))}>
            {metrics.sharpe_ratio.toFixed(2)}
          </p>
          <p className="text-xs text-gray-500">
            Risk-adjusted returns
          </p>
        </div>

        {/* Max Drawdown */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <ArrowTrendingDownIcon className="h-5 w-5 text-red-400" />
            <span className="text-sm font-medium text-gray-400">Max Drawdown</span>
          </div>
          <p className={clsx('text-2xl font-bold', getDrawdownColor(metrics.max_drawdown))}>
            -{metrics.max_drawdown.toFixed(1)}%
          </p>
          <p className="text-xs text-gray-500">
            Largest peak-to-trough decline
          </p>
        </div>

        {/* Current Drawdown */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <ChartBarIcon className="h-5 w-5 text-yellow-400" />
            <span className="text-sm font-medium text-gray-400">Current Drawdown</span>
          </div>
          <p className={clsx('text-2xl font-bold', getDrawdownColor(metrics.current_drawdown))}>
            -{metrics.current_drawdown.toFixed(1)}%
          </p>
          <p className="text-xs text-gray-500">
            Current decline from peak
          </p>
        </div>
      </div>

      {/* Risk Level Indicator */}
      <div className="mt-6 pt-6 border-t border-gray-700">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-400">Overall Risk Level</span>
          <span className={clsx(
            'px-3 py-1 rounded-full text-sm font-medium',
            metrics.sharpe_ratio > 1.5 && metrics.max_drawdown < 10
              ? 'bg-green-900/30 text-green-400'
              : metrics.sharpe_ratio > 1 && metrics.max_drawdown < 15
              ? 'bg-yellow-900/30 text-yellow-400'
              : 'bg-red-900/30 text-red-400'
          )}>
            {metrics.sharpe_ratio > 1.5 && metrics.max_drawdown < 10
              ? 'Low Risk'
              : metrics.sharpe_ratio > 1 && metrics.max_drawdown < 15
              ? 'Medium Risk'
              : 'High Risk'}
          </span>
        </div>
        
        {/* Kelly Criterion */}
        <div className="mt-4">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm text-gray-400">Recommended Kelly %</span>
            <span className="text-sm font-medium">{(metrics.kelly_criterion * 100).toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${Math.min(metrics.kelly_criterion * 100, 100)}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  )
}