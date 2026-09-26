import { load } from "../../lib/db";
import SettingsForm from "./SettingsForm";

export const dynamic = "force-dynamic";

export default function Settings() {
  const db = load();
  return (
    <>
      <h1>Settings</h1>
      <p className="sub">Store-wide preferences.</p>
      <SettingsForm settings={db.settings} />
    </>
  );
}
