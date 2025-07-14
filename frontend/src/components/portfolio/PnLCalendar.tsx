import { useState } from 'react'
import { 
  format, 
  startOfMonth, 
  endOfMonth, 
  eachDayOfInterval,
  isToday,
  addMonths,
  subMonths
} from 'date-fns'
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline'
import { clsx } from 'clsx'

interface DailyPnL {
  date: string
  profit: number
  bets_placed: number
  bets_won: number
  bets_lost: number
}

interface PnLCalendarProps {
  data: DailyPnL[]
}

export const PnLCalendar = ({ data }: PnLCalendarProps) => {
  const [currentMonth, setCurrentMonth] = useState(new Date())

  const monthStart = startOfMonth(currentMonth)
  const monthEnd = endOfMonth(currentMonth)
  const days = eachDayOfInterval({ start: monthStart, end: monthEnd })

  // Create a map for quick lookup
  const pnlMap = new Map(
    data.map(item => [format(new Date(item.date), 'yyyy-MM-dd'), item])
  )

  const getColorForProfit = (profit: number) => {
    if (profit > 100) return 'bg-green-500'
    if (profit > 50) return 'bg-green-400'
    if (profit > 0) return 'bg-green-300'
    if (profit === 0) return 'bg-gray-600'
    if (profit > -50) return 'bg-red-300'
    if (profit > -100) return 'bg-red-400'
    return 'bg-red-500'
  }

  const getDayOfWeek = (index: number) => {
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    return days[index]
  }

  const startDayOfWeek = monthStart.getDay()
  const emptyDays = Array.from({ length: startDayOfWeek }, (_, i) => i)

  const monthlyStats = days.reduce((acc, day) => {
    const dateKey = format(day, 'yyyy-MM-dd')
    const dayData = pnlMap.get(dateKey)
    if (dayData) {
      acc.totalProfit += dayData.profit
      acc.totalBets += dayData.bets_placed
      acc.wonBets += dayData.bets_won
      acc.lostBets += dayData.bets_lost
      if (dayData.profit > 0) acc.profitableDays++
      if (dayData.profit < 0) acc.losingDays++
    }
    return acc
  }, {
    totalProfit: 0,
    totalBets: 0,
    wonBets: 0,
    lostBets: 0,
    profitableDays: 0,
    losingDays: 0
  })

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold">P&L Calendar</h3>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}
            className="p-2 hover:bg-gray-700 rounded transition-colors"
          >
            <ChevronLeftIcon className="h-5 w-5" />
          </button>
          <span className="text-lg font-medium px-3">
            {format(currentMonth, 'MMMM yyyy')}
          </span>
          <button
            onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}
            className="p-2 hover:bg-gray-700 rounded transition-colors"
          >
            <ChevronRightIcon className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Monthly Summary */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-900 rounded-lg p-3">
          <p className="text-sm text-gray-400">Monthly P&L</p>
          <p className={clsx(
            'text-2xl font-bold',
            monthlyStats.totalProfit > 0 ? 'text-green-400' : 'text-red-400'
          )}>
            ${monthlyStats.totalProfit.toFixed(2)}
          </p>
        </div>
        <div className="bg-gray-900 rounded-lg p-3">
          <p className="text-sm text-gray-400">Win Rate</p>
          <p className="text-2xl font-bold">
            {monthlyStats.totalBets > 0 
              ? ((monthlyStats.wonBets / monthlyStats.totalBets) * 100).toFixed(1)
              : '0'}%
          </p>
        </div>
        <div className="bg-gray-900 rounded-lg p-3">
          <p className="text-sm text-gray-400">Profitable Days</p>
          <p className="text-2xl font-bold text-green-400">
            {monthlyStats.profitableDays}/{monthlyStats.profitableDays + monthlyStats.losingDays}
          </p>
        </div>
      </div>

      {/* Calendar Grid */}
      <div className="grid grid-cols-7 gap-1">
        {/* Day headers */}
        {[0, 1, 2, 3, 4, 5, 6].map(day => (
          <div key={day} className="text-center py-2 text-sm font-medium text-gray-400">
            {getDayOfWeek(day)}
          </div>
        ))}

        {/* Empty days */}
        {emptyDays.map(day => (
          <div key={`empty-${day}`} className="aspect-square" />
        ))}

        {/* Calendar days */}
        {days.map(day => {
          const dateKey = format(day, 'yyyy-MM-dd')
          const dayData = pnlMap.get(dateKey)
          const hasData = !!dayData

          return (
            <div
              key={dateKey}
              className={clsx(
                'aspect-square p-2 rounded relative group cursor-pointer transition-all',
                isToday(day) ? 'ring-2 ring-blue-500' : '',
                hasData ? getColorForProfit(dayData.profit) : 'bg-gray-900',
                hasData ? 'hover:opacity-80' : 'hover:bg-gray-800'
              )}
            >
              <div className="text-sm font-medium">
                {format(day, 'd')}
              </div>
              
              {hasData && (
                <>
                  <div className="text-xs mt-1">
                    <p className="font-bold">
                      ${dayData.profit > 0 ? '+' : ''}{dayData.profit.toFixed(0)}
                    </p>
                  </div>

                  {/* Tooltip */}
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                    <div className="bg-gray-900 border border-gray-700 rounded-lg p-3 shadow-xl whitespace-nowrap">
                      <p className="font-medium mb-1">{format(day, 'MMM d, yyyy')}</p>
                      <div className="space-y-1 text-xs">
                        <p>P&L: <span className={dayData.profit > 0 ? 'text-green-400' : 'text-red-400'}>
                          ${dayData.profit.toFixed(2)}
                        </span></p>
                        <p>Bets: {dayData.bets_placed}</p>
                        <p>Won: {dayData.bets_won} | Lost: {dayData.bets_lost}</p>
                        <p>Win Rate: {dayData.bets_placed > 0 
                          ? ((dayData.bets_won / dayData.bets_placed) * 100).toFixed(0)
                          : 0}%
                        </p>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          )
        })}
      </div>

      {/* Legend */}
      <div className="mt-6 pt-6 border-t border-gray-700">
        <p className="text-sm font-medium text-gray-400 mb-2">Daily P&L Scale</p>
        <div className="flex items-center gap-2 text-xs">
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 bg-green-500 rounded"></div>
            <span>&gt;$100</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 bg-green-400 rounded"></div>
            <span>$50-100</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 bg-green-300 rounded"></div>
            <span>$0-50</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 bg-gray-600 rounded"></div>
            <span>$0</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 bg-red-300 rounded"></div>
            <span>-$50-0</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 bg-red-400 rounded"></div>
            <span>-$100--50</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 bg-red-500 rounded"></div>
            <span>&lt;-$100</span>
          </div>
        </div>
      </div>
    </div>
  )
}