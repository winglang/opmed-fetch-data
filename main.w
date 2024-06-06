bring http;
bring expect;
bring "./proactive.w" as proactive;

let proactiveInstance = new proactive.Proactive(
  symmetricKey: "symmetric_key1" ,
  urlSurgeonApp: "url_surgeon_app1",
  sender: "eladc@monada.co",
) as "Proactive";
