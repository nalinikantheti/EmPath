import {getStore} from '@netlify/blobs';
import {handleFeedback} from '../lib/feedback.mjs';
export default async request=>{
 try{return await handleFeedback(request,getStore({name:'empath-community-feedback',consistency:'strong'}));}
 catch(error){console.error('Feedback service unavailable:',error.name);return Response.json({error:'The feedback board is temporarily unavailable. Please try again.'},{status:503,headers:{'Cache-Control':'no-store'}});}
};
