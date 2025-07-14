import { useEffect, useRef } from 'react'
import * as d3 from 'd3'

interface CorrelationMatrixProps {
  data: number[][]
  labels: string[]
}

export const CorrelationMatrix = ({ data, labels }: CorrelationMatrixProps) => {
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (!svgRef.current || !data || data.length === 0) return

    const margin = { top: 80, right: 80, bottom: 80, left: 80 }
    const width = 500 - margin.left - margin.right
    const height = 500 - margin.top - margin.bottom
    const cellSize = width / labels.length

    // Clear previous content
    d3.select(svgRef.current).selectAll('*').remove()

    const svg = d3.select(svgRef.current)
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    // Color scale
    const colorScale = d3.scaleSequential()
      .interpolator(d3.interpolateRdBu)
      .domain([-1, 1])

    // Create cells
    const cells = g.selectAll('.cell')
      .data(data.flatMap((row, i) => 
        row.map((value, j) => ({ value, i, j }))
      ))
      .enter().append('g')
      .attr('class', 'cell')
      .attr('transform', d => `translate(${d.j * cellSize},${d.i * cellSize})`)

    // Add rectangles
    cells.append('rect')
      .attr('width', cellSize - 2)
      .attr('height', cellSize - 2)
      .attr('fill', d => colorScale(d.value))
      .attr('stroke', '#1F2937')
      .attr('stroke-width', 2)
      .on('mouseover', function(event: any, d: any) {
        // Highlight row and column
        d3.selectAll('.cell rect')
          .attr('opacity', (cell: any) => 
            (cell.i === d.i || cell.j === d.j) ? 1 : 0.3
          )
        
        // Show tooltip
        const tooltip = d3.select('body').append('div')
          .attr('class', 'tooltip')
          .style('position', 'absolute')
          .style('background', '#1F2937')
          .style('border', '1px solid #374151')
          .style('border-radius', '4px')
          .style('padding', '8px')
          .style('color', 'white')
          .style('font-size', '12px')
          .style('pointer-events', 'none')
          .style('opacity', 0)

        tooltip.transition()
          .duration(200)
          .style('opacity', 0.9)

        tooltip.html(`
          <strong>${labels[d.i]} × ${labels[d.j]}</strong><br/>
          Correlation: ${d.value.toFixed(3)}
        `)
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 28) + 'px')
      })
      .on('mouseout', function() {
        // Reset opacity
        d3.selectAll('.cell rect').attr('opacity', 1)
        
        // Remove tooltip
        d3.selectAll('.tooltip').remove()
      })

    // Add text values
    cells.append('text')
      .attr('x', cellSize / 2)
      .attr('y', cellSize / 2)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .attr('fill', d => Math.abs(d.value) > 0.5 ? 'white' : '#9CA3AF')
      .attr('font-size', '12px')
      .attr('font-weight', 'bold')
      .text((d: any) => d.value.toFixed(2))

    // Add labels - X axis
    g.selectAll('.x-label')
      .data(labels)
      .enter().append('text')
      .attr('class', 'x-label')
      .attr('x', (_d: any, i: any) => i * cellSize + cellSize / 2)
      .attr('y', -10)
      .attr('text-anchor', 'middle')
      .attr('fill', '#9CA3AF')
      .attr('font-size', '12px')
      .text((d: any) => d)

    // Add labels - Y axis
    g.selectAll('.y-label')
      .data(labels)
      .enter().append('text')
      .attr('class', 'y-label')
      .attr('x', -10)
      .attr('y', (_d: any, i: any) => i * cellSize + cellSize / 2)
      .attr('text-anchor', 'end')
      .attr('dominant-baseline', 'middle')
      .attr('fill', '#9CA3AF')
      .attr('font-size', '12px')
      .text((d: any) => d)

    // Add color legend
    const legendWidth = 200
    const legendHeight = 20

    const legendScale = d3.scaleLinear()
      .domain([-1, 1])
      .range([0, legendWidth])

    const legendAxis = d3.axisBottom(legendScale)
      .ticks(5)
      .tickFormat(d3.format('.1f'))

    const legend = svg.append('g')
      .attr('transform', `translate(${margin.left + width / 2 - legendWidth / 2}, ${height + margin.top + 40})`)

    // Gradient for legend
    const gradient = svg.append('defs')
      .append('linearGradient')
      .attr('id', 'correlation-gradient')
      .attr('x1', '0%')
      .attr('x2', '100%')

    const numStops = 10
    for (let i = 0; i <= numStops; i++) {
      const offset = i / numStops
      const value = -1 + 2 * offset
      gradient.append('stop')
        .attr('offset', `${offset * 100}%`)
        .attr('stop-color', colorScale(value))
    }

    legend.append('rect')
      .attr('width', legendWidth)
      .attr('height', legendHeight)
      .style('fill', 'url(#correlation-gradient)')

    legend.append('g')
      .attr('transform', `translate(0, ${legendHeight})`)
      .call(legendAxis)
      .selectAll('text')
      .attr('fill', '#9CA3AF')

    legend.append('text')
      .attr('x', legendWidth / 2)
      .attr('y', -5)
      .attr('text-anchor', 'middle')
      .attr('fill', '#9CA3AF')
      .attr('font-size', '12px')
      .text('Correlation Coefficient')

  }, [data, labels])

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h3 className="text-xl font-bold mb-4">Bet Correlation Matrix</h3>
      <p className="text-sm text-gray-400 mb-6">
        Shows how your bets correlate with each other. High positive correlation (red) means bets tend to win/lose together.
      </p>
      <div className="flex justify-center">
        <svg ref={svgRef}></svg>
      </div>
    </div>
  )
}