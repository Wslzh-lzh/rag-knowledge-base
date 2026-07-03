import { BookOpen, MessageSquareText, Search, Upload, Users } from "lucide-react";

export const navItems = [
  { href: "/", label: "工作台", icon: BookOpen },
  { href: "/kb", label: "知识库", icon: Users },
  { href: "/chat", label: "问答", icon: MessageSquareText },
  { href: "/search", label: "检索", icon: Search },
  { href: "/login", label: "登录", icon: Upload }
] as const;

