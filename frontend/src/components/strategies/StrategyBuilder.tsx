import { useState } from 'react'
import { Strategy, StrategyRule } from '@/types'
import { PlusIcon, TrashIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface StrategyBuilderProps {
  onSave: (strategy: Omit<Strategy, 'id' | 'created_at'>) => void
  initialStrategy?: Strategy
}

const RULE_TYPES = [
  { value: 'edge', label: 'Edge %', unit: '%' },
  { value: 'kelly', label: 'Kelly Fraction', unit: '%' },
  { value: 'sport', label: 'Sport', unit: '' },
  { value: 'odds', label: 'Odds Range', unit: '' },
  { value: 'time', label: 'Time Window', unit: 'hours' },
]

const OPERATORS = {
  numeric: [
    { value: 'gt', label: 'Greater than' },
    { value: 'lt', label: 'Less than' },
    { value: 'eq', label: 'Equals' },
    { value: 'between', label: 'Between' },
  ],
  categorical: [
    { value: 'in', label: 'In' },
    { value: 'eq', label: 'Equals' },
  ],
}

export const StrategyBuilder = ({ onSave, initialStrategy }: StrategyBuilderProps) => {
  const [name, setName] = useState(initialStrategy?.name || '')
  const [description, setDescription] = useState(initialStrategy?.description || '')
  const [rules, setRules] = useState<StrategyRule[]>(initialStrategy?.rules || [])
  const [isActive, setIsActive] = useState(initialStrategy?.is_active ?? true)

  const addRule = () => {
    const newRule: StrategyRule = {
      id: `rule-${Date.now()}`,
      type: 'edge',
      operator: 'gt',
      value: 5,
      combine_with: rules.length > 0 ? 'AND' : 'AND',
    }
    setRules([...rules, newRule])
  }

  const updateRule = (index: number, updates: Partial<StrategyRule>) => {
    const updatedRules = [...rules]
    updatedRules[index] = { ...updatedRules[index], ...updates }
    setRules(updatedRules)
  }

  const removeRule = (index: number) => {
    setRules(rules.filter((_, i) => i !== index))
  }

  const handleSave = () => {
    if (!name.trim()) {
      toast.error('Strategy name is required')
      return
    }
    if (rules.length === 0) {
      toast.error('At least one rule is required')
      return
    }

    onSave({
      name,
      description,
      rules,
      is_active: isActive,
    })
  }

  const getRuleOperators = (type: string) => {
    return ['sport'].includes(type) ? OPERATORS.categorical : OPERATORS.numeric
  }

  const renderValueInput = (rule: StrategyRule, index: number) => {
    if (rule.type === 'sport') {
      return (
        <select
          value={rule.value}
          onChange={(e) => updateRule(index, { value: e.target.value })}
          className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
        >
          <option value="NFL">NFL</option>
          <option value="NBA">NBA</option>
          <option value="MLB">MLB</option>
          <option value="NHL">NHL</option>
        </select>
      )
    }

    if (rule.operator === 'between') {
      const [min, max] = Array.isArray(rule.value) ? rule.value : [0, 100]
      return (
        <div className="flex items-center gap-2">
          <input
            type="number"
            value={min}
            onChange={(e) => updateRule(index, { value: [Number(e.target.value), max] })}
            className="w-20 bg-gray-900 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
          />
          <span>to</span>
          <input
            type="number"
            value={max}
            onChange={(e) => updateRule(index, { value: [min, Number(e.target.value)] })}
            className="w-20 bg-gray-900 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
          />
        </div>
      )
    }

    return (
      <input
        type="number"
        value={rule.value as number}
        onChange={(e) => updateRule(index, { value: Number(e.target.value) })}
        className="w-24 bg-gray-900 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
      />
    )
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 space-y-6">
      <div>
        <h3 className="text-xl font-bold mb-4">Strategy Builder</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Strategy Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., High Edge NFL Strategy"
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe your strategy..."
              rows={3}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-lg font-semibold">Rules</h4>
          <button
            onClick={addRule}
            className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
          >
            <PlusIcon className="h-4 w-4" />
            Add Rule
          </button>
        </div>

        <div className="space-y-3">
          {rules.length === 0 ? (
            <p className="text-center py-8 text-gray-400">
              No rules added yet. Click "Add Rule" to get started.
            </p>
          ) : (
            rules.map((rule, index) => (
              <div key={rule.id} className="bg-gray-900 rounded-lg p-4">
                <div className="flex items-center gap-3">
                  {index > 0 && (
                    <select
                      value={rule.combine_with}
                      onChange={(e) => updateRule(index, { combine_with: e.target.value as 'AND' | 'OR' })}
                      className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm"
                    >
                      <option value="AND">AND</option>
                      <option value="OR">OR</option>
                    </select>
                  )}

                  <select
                    value={rule.type}
                    onChange={(e) => updateRule(index, { type: e.target.value as any })}
                    className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  >
                    {RULE_TYPES.map((type) => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>

                  <select
                    value={rule.operator}
                    onChange={(e) => updateRule(index, { operator: e.target.value as any })}
                    className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  >
                    {getRuleOperators(rule.type).map((op) => (
                      <option key={op.value} value={op.value}>
                        {op.label}
                      </option>
                    ))}
                  </select>

                  {renderValueInput(rule, index)}

                  {RULE_TYPES.find(t => t.value === rule.type)?.unit && (
                    <span className="text-gray-400">
                      {RULE_TYPES.find(t => t.value === rule.type)?.unit}
                    </span>
                  )}

                  <button
                    onClick={() => removeRule(index)}
                    className="ml-auto p-2 text-red-400 hover:bg-gray-800 rounded transition-colors"
                  >
                    <TrashIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="flex items-center justify-between pt-6 border-t border-gray-700">
        <label className="flex items-center gap-3">
          <input
            type="checkbox"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
            className="w-5 h-5 rounded border-gray-600 text-blue-600 focus:ring-blue-500"
          />
          <span className="font-medium">Active Strategy</span>
        </label>

        <button
          onClick={handleSave}
          className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
        >
          Save Strategy
        </button>
      </div>
    </div>
  )
}