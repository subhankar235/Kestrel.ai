interface PersonaHeaderProps {
  name: string;
  domain: string;
}

export function PersonaHeader({ name, domain }: PersonaHeaderProps) {
  return (
    <header className="sticky top-0 z-10 bg-background/80 backdrop-blur-sm border-b">
      <div className="mx-auto max-w-3xl px-4 py-4">
        <h1 className="text-xl font-bold">{name}</h1>
        <p className="text-sm text-muted-foreground">{domain}</p>
      </div>
    </header>
  );
}
