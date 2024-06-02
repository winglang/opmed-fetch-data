bring cloud;
bring util;
bring http;
bring expect;
bring dynamodb;
bring ses;
bring sns;
bring "./node_modules/@winglibs/python" as python;

pub struct ProactiveProps {
  symmetricKey: str;
  urlSurgeonApp: str;
  sender: str;
}

/// Class to define all infrastructure resources for the proactive feature.
pub class Proactive {
  pub api: cloud.Api;

  new(props: ProactiveProps) {
    let sesClient = new ses.EmailService({});
    let snsClient = new sns.MobileNotifications();
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
    
    let nudgeEnv = {
      SYMMETRIC_KEY: props.symmetricKey,
      URL_SURGEON_APP: props.urlSurgeonApp,
      sender: props.sender,
      URL: this.api.url,
    };

    let resourceEnv = {
      "proactive_blocks_status": "proactive_blocks_status",
      "internal_to_external_ids": "internal_to_external_ids",
    };
    
    this.api.post("/api/v1/:nudge_category/:nudge_method", new python.InflightApiEndpointHandler(
      path: @dirname,
      handler: "proactive_nudge_reminder/nudge_reminder.wing_api_handler",
      lift: {
        ses_client: {
          obj: sesClient,
          allow: ["sendRawEmail"]
        },
        sns_client: {
          obj: snsClient,
          allow: ["publish"]
        },
      }
    ) as "nudge_reminder", env: nudgeEnv);
    
    this.api.put("/api/v1/resources/:block_status_name/bundle", new python.InflightApiEndpointHandler(
      path: @dirname,
      handler: "resources/lambda_function.wing_api_handler",
      lift: {
        proactive_blocks_status: {
          obj: table,
          allow: ["readWriteConnection"]
        }
      }
    ) as "resources_put", env: resourceEnv);
    
    this.api.get("/api/v1/resources/:block_status_name/bundle", new python.InflightApiEndpointHandler(
      path: @dirname,
      handler: "resources/lambda_function.wing_api_handler",
      lift: {
        proactive_blocks_status: {
          obj: table,
          allow: ["readWriteConnection"]
        }
      }
    ) as "resources_get", env: resourceEnv);
  }
}
