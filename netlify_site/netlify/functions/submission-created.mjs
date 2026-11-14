import {connectLambda,getStore} from '@netlify/blobs';
import {saveSubmission} from '../lib/feedback.mjs';
export const handler=async event=>{
 connectLambda(event);
 const {payload}=JSON.parse(event.body||'{}');
 await saveSubmission(payload,getStore({name:'empath-community-feedback',consistency:'strong'}));
 return {statusCode:200,body:'OK'};
};
