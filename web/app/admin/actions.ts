"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { ADMIN_COOKIE, openAdminSession } from "@/lib/admin";

export async function login(formData: FormData) {
  const key = String(formData.get("key") ?? "").trim();
  if (!key) redirect("/admin");
  // The key is traded for a week-long signed session: the browser never keeps it.
  const session = await openAdminSession(key);
  if (typeof session !== "string" || session === "unauthorized" || session === "blocked") {
    redirect(`/admin?error=${session === "blocked" ? "bloqueado" : "clave"}`);
  }
  (await cookies()).set(ADMIN_COOKIE, session, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/admin",
    maxAge: 60 * 60 * 24 * 7,
  });
  redirect("/admin");
}

export async function logout() {
  (await cookies()).delete({ name: ADMIN_COOKIE, path: "/admin" });
  redirect("/admin");
}
