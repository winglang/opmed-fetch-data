bring cloud;
bring util;
bring http;
bring expect;
bring dynamodb;
bring ses;
bring sns;
bring "./node_modules/@winglibs/python" as python;

pub class FetchData {
  pub nudgeReminder: cloud.Function;
  pub api: cloud.Api;

  new() {
    let sesClient = new ses.EmailService({});
    let snsClient = new sns.MobileClient();
    let table = new dynamodb.Table(
      name: "proactive_blocks_status",
      attributes: [
        {
          name: "tenant_id",
          type: "S",
        },
        {
          name: "data_id",
          type: "S",
        },
      ],
      hashKey: "tenant_id",
      rangeKey: "data_id",
    ) as "proactive_blocks_status table";
    
    this.api = new cloud.Api();
    
    let nudgeEnv: MutMap<str> = {
      SYMMETRIC_KEY: "symmetric_key1" ,
      URL_SURGEON_APP: "url_surgeon_app1",
      URL: this.api.url,
      sender: "eladc@monada.co",
    };
    
    this.api.post("/api/v1/:nudge_category/:nudge_method", new python.InflightApiEndpointHandler(
      path: "./",
      handler: "proactive_nudge_reminder/nudge_reminder.send_reminder",
      lift: {
        ses: {
          obj: sesClient,
          allow: ["sendRawEmail"]
        },
        sns: {
          obj: snsClient,
          allow: ["publish"]
        },
      }
    ) as "nudge_reminder", { env: nudgeEnv.copy() });
    
    this.api.put("/api/v1/resources/:block_status_name/bundle", new python.InflightApiEndpointHandler(
      path: "./",
      handler: "resources/lambda_function.lambda_handler",
      lift: {
        proactive_blocks_status: {
          obj: table,
          allow: ["readWriteConnection"]
        }
      }
    ) as "resources_put", { env: {
      "proactive_blocks_status": "proactive_blocks_status",
      "internal_to_external_ids": "internal_to_external_ids",
    } });
    
    this.api.get("/api/v1/resources/:block_status_name/bundle", new python.InflightApiEndpointHandler(
      path: "./",
      handler: "resources/lambda_function.lambda_handler",
      lift: {
        proactive_blocks_status: {
          obj: table,
          allow: ["readWriteConnection"]
        }
      }
    ) as "resources_get", { env: {
      "proactive_blocks_status": "proactive_blocks_status",
      "internal_to_external_ids": "internal_to_external_ids",
    } });
    
    this.nudgeReminder = new cloud.Function(inflight () => {
      let res = http.post(this.api.url + "/api/v1/proactive-block-release/send-email", 
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
  }
}
