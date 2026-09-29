const FOOT_LABELS: Record<string, string> = {
  left: "Zurdo",
  right: "Diestro",
  both: "Ambidiestro",
};

export function footLabel(foot: string): string {
  return FOOT_LABELS[foot] ?? foot;
}

export function formatMarketValue(amountEur: number): string {
  if (amountEur >= 1_000_000) {
    return `${(amountEur / 1_000_000).toFixed(amountEur % 1_000_000 === 0 ? 0 : 1)}M €`;
  }
  if (amountEur >= 1_000) {
    return `${(amountEur / 1_000).toFixed(0)}k €`;
  }
  return `${amountEur} €`;
}

export function calculateAge(dateOfBirth: string): number {
  const birth = new Date(dateOfBirth);
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const hasNotHadBirthdayThisYear =
    today.getMonth() < birth.getMonth() ||
    (today.getMonth() === birth.getMonth() && today.getDate() < birth.getDate());
  if (hasNotHadBirthdayThisYear) {
    age -= 1;
  }
  return age;
}
