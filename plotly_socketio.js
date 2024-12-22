var socket = io()
var traces = {}

socket.on("price_update", function (data) {
  if (!traces[data.product]) {
    traces[data.product] = {
      x: [],
      y: [],
      name: data.product,
      mode: "lines",
      line: { width: 2 },
    }
  }

  var trace = traces[data.product]
  trace.x.push(new Date())
  trace.y.push(data.price)

  if (trace.x.length > 100) {
    trace.x.shift()
    trace.y.shift()
  }

  Plotly.react("live-graph", Object.values(traces), {
    title: "Real-Time Cryptocurrency Prices",
    xaxis: {
      title: "Time",
      range: [trace.x[0], trace.x[trace.x.length - 1]],
    },
    yaxis: { title: "Price (USD)" },
  })
})
