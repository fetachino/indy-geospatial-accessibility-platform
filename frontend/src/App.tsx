const plannedCapabilities = [
  "Compare neighborhood accessibility indicators",
  "Filter public transit and essential-service categories",
  "Inspect transparent methods, source metadata, and limitations",
];

export function App() {
  return (
    <main>
      <section className="hero" aria-labelledby="page-title">
        <p className="eyebrow">Marion County, Indiana</p>
        <h1 id="page-title">Indy Geospatial Accessibility Platform</h1>
        <p className="lede">
          A developing GIS platform for examining access to public transit and
          essential services across Indianapolis neighborhoods.
        </p>
        <p className="status" role="status">
          Milestone 0: project foundation. No analytical results are available
          yet.
        </p>
      </section>

      <section className="capabilities" aria-labelledby="capabilities-title">
        <div>
          <p className="eyebrow">Planned application</p>
          <h2 id="capabilities-title">Evidence before conclusions</h2>
        </div>
        <ul>
          {plannedCapabilities.map((capability) => (
            <li key={capability}>{capability}</li>
          ))}
        </ul>
      </section>

      <aside aria-labelledby="method-note-title">
        <h2 id="method-note-title">Method note</h2>
        <p>
          Future proximity measures will not be described as walking routes.
          Network accessibility will be modeled and reported separately when
          suitable routing data are available.
        </p>
      </aside>
    </main>
  );
}
