# TrackerSupport mixin

from __future__ import nested_scopes
import os, string, re
from string import join, split, strip

import DocumentTemplate
from AccessControl import getSecurityManager, ClassSecurityInfo
import Permissions
from Globals import package_home

from Utils import BLATHER,formattedTraceback
from Defaults import ISSUE_CATEGORIES, ISSUE_SEVERITIES, ISSUE_STATUSES, \
     ISSUE_COLOURS

ISSUE_FORM = DocumentTemplate.HTML ('''
<!-- start of issue property form -->
<form action="&dtml-page_url;/changeIssueProperties" method="post">
<table border="0" cellspacing="0" cellpadding="5"
bgcolor="&dtml-issueColour;">
<tr><td>
**Description:**
<b><input type="text" name="title" value="<dtml-var "title[12:]" missing html_quote>" size="50" maxlength="200" style="font-weight:bold"></b>
<dtml-let
  highnumber="0#_.int(Catalog(isIssue=1,sort_on='id')[-2].id[7:11])"
  thisnumber="_.int(id()[7:11])"
  previous="'IssueNo'+_.string.zfill(thisnumber-1,4)"
  next="'IssueNo'+_.string.zfill(thisnumber+1,4)"
  issue_categories="_.getattr(this(),'issue_categories','') or \
                    ['general']"
  issue_severities="_.getattr(this(),'issue_severities','') or \
                    ['serious','normal','wishlist']"
  issue_statuses="_.getattr(this(),'issue_statuses','') or \
                    ['open','closed']"
>
<dtml-comment>
<a href="&dtml-previous;">&lt;&lt;</a>&nbsp;<a <dtml-try>
href="<dtml-var "pageWithName(parents[0]).getId()">?&dtml-QUERY_STRING;">^^</a>&nbsp;<a 
<dtml-except></dtml-try>href="&dtml-next;">&gt;&gt;</a>
</dtml-comment>
<br>
**Category:**
<select name="category">
<dtml-in issue_categories prefix=x>
<option <dtml-if "category==x_sequence_item">selected</dtml-if>>
&dtml-x_sequence_item;</option>
</dtml-in>
</select> 
**Severity:**
<select name="severity">
<dtml-in issue_severities prefix=x>
<option <dtml-if "severity==x_sequence_item">selected</dtml-if>>
&dtml-x_sequence_item;</option>
</dtml-in>
</select> 
**Status:**
<select name="status">
<dtml-in issue_statuses prefix=x>
<option <dtml-if "status==x_sequence_item">selected</dtml-if>>
&dtml-x_sequence_item;</option>
</dtml-in>
</select>
</dtml-let>
<br><b>Optional note:</b> <input type="text" name="log" value="" size="55" maxlength="55">&nbsp;
<input name="submit" type="submit" value="Change">
<br>
**Submitted by:**
<dtml-var "_.getattr(this(),'creator','') or '(unknown)'">
**at:**
<dtml-var creation_time missing=""><dtml-let
creation_time="_.getattr(this(),'creation_time','')"
creation="_.DateTime(_.getattr(this(),'creation_time','') or 1007105000)"
current="_.DateTime(ZopeTime().strftime('%Y/%m/%d %H:%M:%S'))"
elapsed="current-creation"
hourfactor="0.041666666666666664"
minutefactor="0.00069444444444444447"
secondsfactor="1.1574074074074073e-05"
days="_.int(_.math.floor(elapsed))"
weeks="days / 7"
months="days / 30"
years="days / 365"
hours="_.int(_.math.floor((elapsed-days)/hourfactor))"
minutes="_.int(_.math.floor((elapsed-days-hourfactor*hours)/minutefactor))"
seconds="_.int(_.round((elapsed-days-hourfactor*hours-minutefactor*minutes)/secondsfactor))"
>(<dtml-unless creation_time>unknown, ></dtml-unless><dtml-if years>
<dtml-var years> year<dtml-var "years > 1 and 's' or ''">
<dtml-elif months>
<dtml-var months> month<dtml-var "months > 1 and 's' or ''">
<dtml-elif weeks>
<dtml-var weeks> week<dtml-var "weeks > 1 and 's' or ''">
<dtml-elif days>
<dtml-var days> day<dtml-var "days > 1 and 's' or ''">
<dtml-elif hours>
<dtml-var hours> hour<dtml-var "hours > 1 and 's' or ''">
<dtml-elif minutes>
<dtml-var minutes> minute<dtml-var "minutes > 1 and 's' or ''">
<dtml-else>
<dtml-var seconds> second<dtml-var "seconds > 1 and 's' or ''">
</dtml-if> ago)
</dtml-let>
<br>
**Details & comments:**
</td></tr></table>
</form>
<!-- end of issue property form -->
''')

class TrackerSupport:
    """
    This mix-in class adds some methods to ZWikiPage to facilitate
    wiki-based issue trackers.
    """
    security = ClassSecurityInfo()
    
    security.declareProtected(Permissions.View, 'isIssue')
    def isIssue(self,client=None,REQUEST=None,RESPONSE=None,**kw):
        """
        Return true if this page is a tracker issue.

        In the past pages with a special page type were issues. Now, any
        page named "IssueNo.." is an issue. (and, whose type supports
        issue properties ? No never mind that)

        Flexibility will be useful here so this method may be overridden
        with a DTML method (XXX or python script).
        """
        if hasattr(self.folder(), 'isIssue'):
            return self.folder().isIssue(self,REQUEST)
        else:
            if (re.match(r'^IssueNo',self.title_or_id())
                or self.pageTypeId() == 'issuedtml'): # backwards compatibility
                return 1
            else:
                return 0

    security.declareProtected(Permissions.View, 'issueCount')
    def issueCount(self):
        return len(filter(lambda x:x[:7]=='IssueNo',self.pageIds()))

    security.declareProtected(Permissions.View, 'hasIssues')
    def hasIssues(self): # likely.
        return self.issueCount() > 0

    security.declareProtected(Permissions.View, 'addIssueFormTo')
    def addIssueFormTo(self,body):
        """
        Add an issue property form above the rendered page text.
        """
        REQUEST = getattr(self,'REQUEST',None)
        return self.stxToHtml(ISSUE_FORM.__call__(self, REQUEST)) + body
            
    security.declareProtected(Permissions.View, 'issueColour')
    def issueColour(self):
        """
        Tell the appropriate issue colour for this page.
        """
        # don't acquire these
        return self.issueColourFor(
            getattr(getattr(self,'aq_base',self),'category',''),
            getattr(getattr(self,'aq_base',self),'severity',''),
            getattr(getattr(self,'aq_base',self),'status',''),
            )

    security.declareProtected(Permissions.View, 'issueColourFor')
    def issueColourFor(self, category='', severity='', status=''):
        """
        Choose an issue colour based on issue properties.

        Finds the best match in a list of strings like
        "category,status,severity,colour", any of which may be empty.  The
        defaults can be overridden with an 'issue_colours' folder lines
        property.

        If no match is found in the colour list, returns the empty string.
        """
        category, status, severity = map(lambda x:x.strip(),
                                         (category, status, severity))
        # can't figure out a reasonable way to do this without python 2.1
        # convert the strings into dictionaries
        colours = getattr(self.folder(),'issue_colours',ISSUE_COLOURS)
        colours = filter(lambda x:x.strip(),colours)
        l = []
        for i in colours:
            a, b, c, d = map(lambda x:x.strip(),i.split(','))
            l.append({
                'category':a,
                'status':b,
                'severity':c,
                'colour':d,
                })
        # find the most specific match
        l = l and (filter(lambda x:x['category']==category, l) or
                   filter(lambda x:x['category']=='', l))
        l = l and (filter(lambda x:x['status']==status, l) or
                   filter(lambda x:x['status']=='', l))
        l = l and (filter(lambda x:x['severity']==severity, l) or
                   filter(lambda x:x['severity']=='', l))
        if not l:
            return ''
        else:
            return l[0]['colour']
    
    security.declareProtected(Permissions.Add, 'createIssue')
    def createIssue(self, pageid, text=None, title='',
                    category=None, severity=None, status=None, REQUEST=None):
        """
        Convenience method for creating an issue page.

        Security notes: create will check for page creation permission.
        Sets title/category/severity/status properties without requiring
        Manage properties permission.

        As of 0.17, issue pages are named "IssueNoNNNN issue description".
        These arguments should be cleaned up to reflect that, eg title
        should come from pageid and should be called description.  pageid
        should be called pagename.

        We should be able to do without this method.

        XXX clean up
        """
        self.create(pageid,text=text,REQUEST=REQUEST)
        issue = self.pageWithName(pageid)
        issue.manage_addProperty('category','issue_categories','selection')
        issue.manage_addProperty('severity','issue_severities','selection')
        issue.manage_addProperty('status','issue_statuses','selection')
        issue.manage_changeProperties(#page_type='stxprelinkdtmlfitissuehtml',
                                      title=title,
                                      category=category,
                                      severity=severity,
                                      status=status
                                      )
        self.reindex_object()

    security.declareProtected(Permissions.Add, 'createNextIssue')
    def createNextIssue(self, description, text=None,
                        category=None, severity=None, status=None,
                        REQUEST=None):
        """
        Create a new issue page, using the next available issue number.
        """
        # XXX just copied directly from IssueTracker
        try:
            lastid = self.pages(isIssue=1,sort_on='id')[-1].id
            lastnumber = int(lastid[7:11])
            newnumber = lastnumber+1
            newid = 'IssueNo'+string.zfill(newnumber,4)
        except:
            newid = 'IssueNo0001'
        pagename=newid+' '+description
        return self.createIssue(pagename, text, pagename, 
                                category, severity, status, REQUEST)

    #def changeProperties(self, REQUEST=None, **kw):
    #    """
    #    Similar to manage_changeProperties, except redirects back to the
    #    current page. Also restores the issue number which we previously
    #    stripped from title.
    #    
    #    security issue: bypasses Manage properties permission
    #    
    #    Deprecated, useful for backwards compatibility or remove ?
    #    """
    #    if REQUEST is None:
    #        props={}
    #    else: props=REQUEST
    #    if kw:
    #        for name, value in kw.items():
    #            props[name]=value
    #    props['title'] = self.getId()[:11]+' '+props['title']
    #    propdict=self.propdict()
    #    for name, value in props.items():
    #        if self.hasProperty(name):
    #            if not 'w' in propdict[name].get('mode', 'wd'):
    #                raise 'BadRequest', '%s cannot be changed' % name
    #            self._updateProperty(name, value)
    #
    #    self.setLastEditor(REQUEST)
    #    self.reindex_object()
    #    if REQUEST:
    #        REQUEST.RESPONSE.redirect(self.page_url())
            
    def changeIssueProperties(self, title=None, category=None, severity=None, 
                              status=None, log=None, REQUEST=None):
        """
        Change an issue page's properties and redirect back there.

        Also, add a comment to the page describing what was done.

        It expects title to be the issue description, not the complete
        page name.  Changing this will trigger a page rename, which may be
        slow.
        
        XXX security: allows title/category/severity/status properties to
        be set without Manage properties permission.

        XXX upgrade issue: calling this before upgrading an issue to
        a 0.17-style page id will mess up the id/title.
        """
        comment = ''
        if title:
            title = self.getId()[:11]+' '+title
            if title != self.title_or_id():
                comment += "Title: '%s' => '%s' \n" % (self.title_or_id(),title)
            self.rename(title,updatebacklinks=1,sendmail=0,REQUEST=REQUEST)
        if category:
            if category != self.category:
                comment += "Category: %s => %s \n" % (self.category,category)
            self.manage_changeProperties(category=category)
        if severity:
            if severity != self.severity:
                comment += "Severity: %s => %s \n" % (self.severity,severity)
            self.manage_changeProperties(severity=severity)
        if status:
            if status != self.status:
                comment += "Status: %s => %s \n" % (self.status,status)
            self.manage_changeProperties(status=status)
        log = log or 'property change'
        self.comment(text=comment, subject_heading=log, REQUEST=REQUEST)
        self.setLastEditor(REQUEST)
        self.reindex_object()
        if REQUEST:
            REQUEST.RESPONSE.redirect(self.page_url())

    def category_index(self):
        """helper method to facilitate sorting catalog results"""
        try:
            return 1 + list(self.issue_categories).index(self.category)
        except (AttributeError,ValueError):
            return 0
        
    def severity_index(self):
        """helper method to facilitate sorting catalog results"""
        try:
            return 1 + list(self.issue_severities).index(self.severity)
        except (AttributeError,ValueError):
            return 0

    def status_index(self):
        """helper method to facilitate sorting catalog results"""
        try:
            return 1 + list(self.issue_statuses).index(self.status)
        except (AttributeError,ValueError):
            return 0

    # setup methods

    security.declareProtected('Manage properties', 'setupTracker')
    def setupTracker(self,REQUEST=None,pages=0):
        """
        Configure this wiki for issue tracking.

        This
        - sets up the necessary extra catalog fields
        - sets up issue_* folder properties, for customizing
        - creates a dummy issue, if needed, to activate the issue links/tabs
        - if pages=1, installs forms as DTML pages, for easy customizing
        
        Safe to call more than once; will ignore any already existing
        items.  Based on the setupIssueTracker.py external method and the
        data at http://zwiki.org/ZwikiAndZCatalog.
        """
        TextIndexes = [
            ]
        FieldIndexes = [
            'category',
            'category_index',
            'isIssue',
            'severity',
            'severity_index',
            'status',
            'status_index',
            ]
        KeywordIndexes = [
            ]
        DateIndexes = [
            ]
        PathIndexes = [
            ]
        metadata = [
            'category',
            'category_index',
            'issueColour',
            'severity',
            'severity_index',
            'status',
            'status_index',
            ]
        # make sure we have a basic zwiki catalog set up
        self.setupCatalog(reindex=0)
        catalog = self.catalog()
        catalogindexes, catalogmetadata = catalog.indexes(), catalog.schema()
        PluginIndexes = catalog.manage_addProduct['PluginIndexes']
        # add indexes,
        for i in TextIndexes:
            if not i in catalogindexes: PluginIndexes.manage_addTextIndex(i)
        for i in FieldIndexes:
            if not i in catalogindexes: PluginIndexes.manage_addFieldIndex(i)
        for i in KeywordIndexes:
            if not i in catalogindexes: PluginIndexes.manage_addKeywordIndex(i)
        for i in DateIndexes:
            if not i in catalogindexes: PluginIndexes.manage_addDateIndex(i)
        for i in PathIndexes:
            if not i in catalogindexes: PluginIndexes.manage_addPathIndex(i)
        # metadata,
        for m in metadata:
            if not m in catalogmetadata: catalog.manage_addColumn(m)
        # properties,
        self.upgradeFolderIssueProperties()
        # dtml pages,
        if pages:
            dir = package_home(globals())+os.sep+'content'+os.sep+'tracker'+os.sep
            for page in ['IssueTracker','FilterIssues']:
                if not self.pageWithName(page):
                    self.create(page,text=open(dir+page+'.stxdtml','r').read())
        # index each page, to make all indexes and metadata current
        # may duplicate some work in setupCatalog
        n = 0
        cid = self.catalog().getId()
        for p in self.pageObjects():
            n = n + 1
            try:
                BLATHER('indexing page #%d %s in %s'%(n,p.id(),cid))
                p.index_object(log=0)
            except:
                BLATHER('failed to index page #%d %s: %s' \
                        % (n,p.id(),formattedTraceback()))
        BLATHER('indexing complete, %d pages processed' % n)
        # and a dummy issue to enable site navigation links
        if not self.hasIssues():
            self.createNextIssue(
                'first issue',
                'This issue was created to activate the issue tracker links/tabs. You can re-use it.',
                ISSUE_CATEGORIES[-1],
                ISSUE_SEVERITIES[-1],
                ISSUE_STATUSES[-1],
                REQUEST=REQUEST)
        if REQUEST: REQUEST.RESPONSE.redirect(self.trackerUrl())

    def upgradeFolderIssueProperties(self):
        """
        Upgrade issue tracker related properties on the wiki folder if needed.

        Currently just adds properties if missing.
        """
        folder = self.folder()
        existingprops = map(lambda x:x['id'], folder._properties)
        for prop, values in [
            ['issue_categories',ISSUE_CATEGORIES],
            ['issue_severities',ISSUE_SEVERITIES],
            ['issue_statuses',ISSUE_STATUSES],
            ['issue_colours',ISSUE_COLOURS],
            ]:
            if not prop in existingprops:
                folder.manage_addProperty(prop,join(values,'\n'),'lines')
                    
    def upgradeIssueProperties(self):
        """
        Upgrade tracker related properties on this page (and folder) if needed.

        Returns non-zero if we changed any page properties, to help
        upgrade() efficiency.
        """
        changed = 0
        if self.isIssue():
            # check folder first so our selection properties will work
            self.upgradeFolderIssueProperties()
            
            existingprops = map(lambda x:x['id'], self._properties)
            for prop, values, default in [
                ['category','issue_categories',None],
                ['severity','issue_severities','normal'],
                ['status','issue_statuses',None],
                ]:
                if not prop in existingprops:
                    self.manage_addProperty(prop,values,'selection')
                    if default: setattr(self,prop,default)
                    changed = 1
        return changed

