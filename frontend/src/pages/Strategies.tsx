import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import { Strategy } from '@/types'
import { StrategyBuilder } from '@/components/strategies/StrategyBuilder'
import { 
  PlayIcon, 
  PauseIcon, 
  TrashIcon,
  PencilIcon,
  ChartBarIcon,
  PlusIcon
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import { clsx } from 'clsx'

export const Strategies = () => {
  const [showBuilder, setShowBuilder] = useState(false)
  const [editingStrategy, setEditingStrategy] = useState<Strategy | null>(null)

  // Fetch strategies
  const { data: strategies, refetch } = useQuery({
    queryKey: ['strategies'],
    queryFn: async () => {
      const { data } = await apiClient.get<Strategy[]>('/strategies')
      return data
    },
  })

  // Create strategy mutation
  const createStrategy = useMutation({
    mutationFn: async (strategy: Omit<Strategy, 'id' | 'created_at'>) => {
      const { data } = await apiClient.post('/strategies', strategy)
      return data
    },
    onSuccess: () => {
      toast.success('Strategy created successfully')
      setShowBuilder(false)
      refetch()
    },
  })

  // Update strategy mutation
  const updateStrategy = useMutation({
    mutationFn: async ({ id, ...updates }: Partial<Strategy> & { id: string }) => {
      const { data } = await apiClient.put(`/strategies/${id}`, updates)
      return data
    },
    onSuccess: () => {
      toast.success('Strategy updated')
      refetch()
    },
  })

  // Delete strategy mutation
  const deleteStrategy = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/strategies/${id}`)
    },
    onSuccess: () => {
      toast.success('Strategy deleted')
      refetch()
    },
  })

  const handleToggleActive = (strategy: Strategy) => {
    updateStrategy.mutate({
      id: strategy.id,
      is_active: !strategy.is_active,
    })
  }

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this strategy?')) {
      deleteStrategy.mutate(id)
    }
  }

  const handleSaveStrategy = (strategy: Omit<Strategy, 'id' | 'created_at'>) => {
    if (editingStrategy) {
      updateStrategy.mutate({ id: editingStrategy.id, ...strategy })
      setEditingStrategy(null)
    } else {
      createStrategy.mutate(strategy)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Automated Strategies</h1>
          <p className="text-gray-400 mt-1">
            Create and manage automated betting strategies
          </p>
        </div>
        <button
          onClick={() => {
            setEditingStrategy(null)
            setShowBuilder(!showBuilder)
          }}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
        >
          <PlusIcon className="h-5 w-5" />
          New Strategy
        </button>
      </div>

      {(showBuilder || editingStrategy) && (
        <StrategyBuilder
          onSave={handleSaveStrategy}
          initialStrategy={editingStrategy || undefined}
        />
      )}

      {/* Active Strategies */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold">Your Strategies</h2>
        
        {strategies && strategies.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {strategies.map((strategy) => (
              <div
                key={strategy.id}
                className={clsx(
                  'bg-gray-800 rounded-lg p-6 border-2 transition-colors',
                  strategy.is_active ? 'border-green-600' : 'border-gray-700'
                )}
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold">{strategy.name}</h3>
                    <p className="text-sm text-gray-400 mt-1">{strategy.description}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleToggleActive(strategy)}
                      className={clsx(
                        'p-2 rounded transition-colors',
                        strategy.is_active
                          ? 'bg-green-900/30 text-green-400 hover:bg-green-900/50'
                          : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                      )}
                      title={strategy.is_active ? 'Pause Strategy' : 'Activate Strategy'}
                    >
                      {strategy.is_active ? (
                        <PauseIcon className="h-5 w-5" />
                      ) : (
                        <PlayIcon className="h-5 w-5" />
                      )}
                    </button>
                    <button
                      onClick={() => {
                        setEditingStrategy(strategy)
                        setShowBuilder(false)
                      }}
                      className="p-2 text-gray-400 hover:bg-gray-700 rounded transition-colors"
                      title="Edit Strategy"
                    >
                      <PencilIcon className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => handleDelete(strategy.id)}
                      className="p-2 text-red-400 hover:bg-red-900/30 rounded transition-colors"
                      title="Delete Strategy"
                    >
                      <TrashIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>

                {/* Rules Display */}
                <div className="space-y-2 mb-4">
                  <p className="text-sm font-medium text-gray-400">Rules:</p>
                  {strategy.rules.map((rule, index) => (
                    <div key={rule.id} className="text-sm bg-gray-900 rounded px-3 py-2">
                      {index > 0 && (
                        <span className="text-blue-400 font-medium mr-2">
                          {rule.combine_with}
                        </span>
                      )}
                      <span className="text-gray-300">
                        {rule.type} {rule.operator} {
                          Array.isArray(rule.value) 
                            ? rule.value.join(' - ')
                            : rule.value
                        }
                      </span>
                    </div>
                  ))}
                </div>

                {/* Backtest Results */}
                {strategy.backtest_results && (
                  <div className="grid grid-cols-3 gap-3 pt-4 border-t border-gray-700">
                    <div>
                      <p className="text-xs text-gray-400">Win Rate</p>
                      <p className="text-lg font-semibold text-green-400">
                        {strategy.backtest_results.win_rate.toFixed(1)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-400">ROI</p>
                      <p className="text-lg font-semibold text-blue-400">
                        {strategy.backtest_results.roi.toFixed(1)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-400">Profit</p>
                      <p className="text-lg font-semibold">
                        ${strategy.backtest_results.total_profit.toFixed(0)}
                      </p>
                    </div>
                  </div>
                )}

                <div className="mt-4 flex justify-end">
                  <button className="flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300">
                    <ChartBarIcon className="h-4 w-4" />
                    View Backtest
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-gray-800 rounded-lg p-12 text-center">
            <p className="text-gray-400 mb-4">No strategies created yet</p>
            <button
              onClick={() => setShowBuilder(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              <PlusIcon className="h-5 w-5" />
              Create Your First Strategy
            </button>
          </div>
        )}
      </div>

      {/* Strategy Performance Summary */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-xl font-bold mb-4">Strategy Performance</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-400">Active Strategies</p>
            <p className="text-2xl font-bold text-green-400">
              {strategies?.filter(s => s.is_active).length || 0}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-400">Total Bets Placed</p>
            <p className="text-2xl font-bold">1,234</p>
          </div>
          <div>
            <p className="text-sm text-gray-400">Strategy Win Rate</p>
            <p className="text-2xl font-bold text-blue-400">62.5%</p>
          </div>
          <div>
            <p className="text-sm text-gray-400">Strategy Profit</p>
            <p className="text-2xl font-bold text-green-400">+$4,567</p>
          </div>
        </div>
      </div>
    </div>
  )
}