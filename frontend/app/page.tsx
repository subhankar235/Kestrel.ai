import { ApiDemo } from "@/components/landing/api-demo";
import { Architecture } from "@/components/landing/architecture";
import { Hero } from "@/components/landing/hero";
import { LiveFeed } from "@/components/landing/live-feed";
import { Loop } from "@/components/landing/loop";
import { Nav } from "@/components/layout/nav";
import { Footer, StackAndWhy } from "@/components/landing/stack-and-why";

export default function Index() {
  return (
    <div className="relative min-h-screen">
      <Nav />
      <main>
        <Hero />
        <LiveFeed />
        <Loop />
        <Architecture />
        <ApiDemo />
        <StackAndWhy />
      </main>
      <Footer />
    </div>
  );
}
