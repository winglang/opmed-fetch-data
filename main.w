bring http;
bring expect;
bring "./infra.w" as infra;

let proactive = new infra.Proactive() as "Proactive";
let nudgeReminderClient = new infra.NudgeReminder(proactive.api) as "Nudge Reminder Client";

new std.Test(inflight () => {
  nudgeReminderClient.proactiveBlockSendEmail.invoke();

  let res2 = http.get(proactive.api.url + "/api/v1/resources/proactive_blocks_status/bundle?ids=blockId1", 
    headers: {
      "gmix_serviceid": "gmix_serviceid1",
      "referer": "referer1",
      "cookie": "cookie1",
      "tenant-id": "opmed-sandbox",
      "user-id": "user-id1",
    },
  );

  let item = Json.parse(res2.body);
  expect.equal(item["tenant_id"], "opmed-sandbox");
  expect.equal(item["data_id"], "blockId1");
  expect.equal(item["doctorId"], "doctor_id1");
}, timeout: 3m) as "test nudge flow";
