type Props = {
  title: string;
  description: string;
};

export function ComingSoon({ title, description }: Props) {
  return (
    <section className="coming-soon" aria-labelledby="coming-soon-title">
      <h2 id="coming-soon-title">{title}</h2>
      <p>{description}</p>
      <p>
        <strong>Coming Soon</strong> — this route is scaffolded only. Full
        scheduling, offline sync, signatures, and AI report generation are not
        implemented yet.
      </p>
    </section>
  );
}
