"use client";

import { useState } from "react";
import { Field, formValues, useJsonForm } from "../../components/forms";

export default function SettingsForm({ settings }) {
  const [saved, setSaved] = useState(false);
  const { errors, busy, submit } = useJsonForm("/api/settings", { onDone: (_d, r) => { setSaved(true); r.refresh(); } });
  return (
    <form className="card" noValidate onSubmit={(e) => { e.preventDefault(); setSaved(false); submit(formValues(e.currentTarget)); }}>
      <Field label="Store name" name="storeName" error={errors.storeName}>{(id) => <input id={id} name="storeName" defaultValue={settings.storeName} data-testid="settings-store-name" />}</Field>
      <Field label="Currency" name="currency">{(id) => (
        <select id={id} name="currency" defaultValue={settings.currency} data-testid="settings-currency">
          <option value="USD">US dollar (USD)</option><option value="EUR">Euro (EUR)</option><option value="GBP">Pound sterling (GBP)</option>
        </select>
      )}</Field>
      <Field label="Low-stock threshold" name="lowStockThreshold" error={errors.lowStockThreshold} hint="Products at or below this stock level are highlighted.">
        {(id) => <input id={id} name="lowStockThreshold" defaultValue={settings.lowStockThreshold} data-testid="settings-threshold" />}
      </Field>
      <div className="field check">
        <input id="f-emailNotifications" name="emailNotifications" type="checkbox" defaultChecked={settings.emailNotifications} data-testid="settings-notifications" />
        <label htmlFor="f-emailNotifications">Notify me about new orders</label>
      </div>
      <div className="actions">
        <button className="btn primary" type="submit" disabled={busy} data-testid="save-settings">Save settings</button>
        {saved && <span role="status">Settings saved.</span>}
      </div>
    </form>
  );
}
