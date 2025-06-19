export function DashboardHeader() {
  return (
    <div className="text-center mb-8">
      <h1 className="text-3xl md:text-4xl font-bold text-gray-800 border-b-3 border-blue-500 pb-3 mb-4">
        Amazon Dimmers & Light Switches
        <br />
        Competitor Analysis Report
      </h1>

      <div className="text-gray-500 italic">
        Report Generated:{" "}
        {new Date().toLocaleDateString("en-US", {
          month: "long",
          day: "numeric",
          year: "numeric",
          hour: "numeric",
          minute: "numeric",
          hour12: true,
        })}
      </div>
    </div>
  )
}
