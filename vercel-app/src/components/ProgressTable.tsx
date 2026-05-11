"use client";

import type { CrossRow } from "@/lib/kpi";

interface Props {
  rows: CrossRow[];
}

export function ProgressTable({ rows }: Props) {
  const totalRow = rows.reduce(
    (acc, r) => {
      acc.total += r.total;
      acc.ship += r.ship;
      acc.install += r.install;
      acc.weightT += r.weightT;
      return acc;
    },
    { total: 0, ship: 0, install: 0, weightT: 0 },
  );
  const shipPct = totalRow.total ? round1((100 * totalRow.ship) / totalRow.total) : 0;
  const installPct = totalRow.total ? round1((100 * totalRow.install) / totalRow.total) : 0;

  return (
    <div className="card overflow-auto" style={{ maxHeight: "100%" }}>
      <div className="sect-label" style={{ marginBottom: "0.35rem" }}>
        호기 × Zone 진척 현황
      </div>
      <table className="dash-table">
        <thead>
          <tr>
            <th>호기</th>
            <th>Zone</th>
            <th className="num">계획</th>
            <th className="num">발송</th>
            <th className="num">발송율</th>
            <th className="num">시공</th>
            <th className="num">시공율</th>
            <th className="num">중량(t)</th>
          </tr>
        </thead>
        <tbody>
          <tr className="total">
            <td>Total</td>
            <td>-</td>
            <td className="num">{totalRow.total.toLocaleString()}</td>
            <td className="num">{totalRow.ship.toLocaleString()}</td>
            <td className="num">{shipPct}%</td>
            <td className="num">{totalRow.install.toLocaleString()}</td>
            <td className="num">{installPct}%</td>
            <td className="num">{round1(totalRow.weightT).toLocaleString()}</td>
          </tr>
          {rows.map((r, i) => (
            <tr key={`${r.hoki}-${r.zone}-${i}`}>
              <td>{r.hoki}</td>
              <td>{r.zone}</td>
              <td className="num">{r.total.toLocaleString()}</td>
              <td className="num">{r.ship.toLocaleString()}</td>
              <td className="num">{r.shipPct}%</td>
              <td className="num">{r.install.toLocaleString()}</td>
              <td className="num">{r.installPct}%</td>
              <td className="num">{r.weightT.toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function round1(n: number) {
  return Math.round(n * 10) / 10;
}
