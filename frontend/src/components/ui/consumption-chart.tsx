import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'

interface ConsumptionData {
  hour: number
  consumption: number
}

interface ConsumptionChartProps {
  data: ConsumptionData[]
  chartType: 'line' | 'bar'
}

export function ConsumptionChart({ data, chartType }: ConsumptionChartProps) {
  const ChartComponent = chartType === 'line' ? LineChart : BarChart
  const DataComponent = chartType === 'line' ? Line : Bar

  return (
    <ResponsiveContainer width="100%" height={400}>
      <ChartComponent data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="hour"
          label={{ value: 'Hour', position: 'insideBottom', offset: -5 }}
          type="number"
          domain={[0, 23]}
          ticks={[0, 6, 12, 18, 23]}
        />
        <YAxis
          label={{ value: 'Energy (kWh)', angle: -90, position: 'insideLeft' }}
        />
        <Tooltip
          formatter={(value: number) => [`${value.toFixed(2)} kWh`, 'Consumption']}
          labelFormatter={(hour: number) => `Hour ${hour}:00`}
        />
        <DataComponent
          type="monotone"
          dataKey="consumption"
          stroke="#8884d8"
          fill="#8884d8"
          strokeWidth={2}
        />
      </ChartComponent>
    </ResponsiveContainer>
  )
}