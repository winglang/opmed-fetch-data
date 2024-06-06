bring cloud;
bring http;
bring expect;
bring "./proactive.w" as proactive;

let proactiveInstance = new proactive.Proactive(
  symmetricKey: "symmetric_key1" ,
  urlSurgeonApp: "url_surgeon_app1",
  sender: "eladc@monada.co",
) as "Proactive";

let proactiveBlockSendEmail = new cloud.Function(inflight () => {
  let res = http.post(proactiveInstance.api.url + "/api/v1/proactive-block-release/send-email", 
    headers: {
      "gmix_serviceid": "gmix_serviceid1",
      "referer": "referer1",
      "cookie": "cookie1",
      "tenant-id": "opmed-sandbox",
      "user-id": "user-id1",
    },
    body: Json.stringify({
      blocks: [{
        blockId: "blockId1",
        start: "2011-10-05T14:48:00.000Z",
      }],
      doctorName: "doctor_name1",
      doctorId: "doctor_id1",
      content: "content1",
      recipients: ["eladc@monada.co"],
    }),
  );
  log(res.body);
}) as "invoke nudge_reminder";

new std.Test(inflight () => {
  proactiveBlockSendEmail.invoke();

  let res2 = http.get(proactiveInstance.api.url + "/api/v1/resources/proactive_blocks_status/bundle?ids=blockId1", 
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
