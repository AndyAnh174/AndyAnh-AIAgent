export const siteConfig = {
  name: "AI Life Companion",
  url: process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000",
  description: "Your intelligent journal and digital twin powered by AI",
  links: {
    github: "https://github.com",
  },
};

export type SiteConfig = typeof siteConfig;
