# -*- coding: UTF-8 -*-
from pdoauth.models.User import User
from pdoauth.models.Assurance import Assurance
import time
from test.helpers.PDUnitTest import PDUnitTest, test
from pdoauth.ReportedError import ReportedError
from test.helpers.UserUtil import UserUtil
from test.helpers.CryptoTestUtil import CryptoTestUtil
from integrationtest.helpers.UserTesting import UserTesting
from pdoauth.models.KeyData import KeyData
from pdoauth.models.TokenInfoByAccessKey import TokenInfoByAccessKey
from pdoauth.models.Application import Application
from pdoauth.AuthProvider import AuthProvider
from test import config

class UserInfoTest(PDUnitTest, UserUtil, CryptoTestUtil):

    def setUp(self):
        PDUnitTest.setUp(self)
        self.createLoggedInUser()

    @test
    def logged_in_user_can_get_its_info(self):
        resp = self.showUserByCurrentUser('me')
        self.assertEquals(resp.status_code, 200)
        data = self.fromJson(resp)
        self.assertTrue(data.has_key('userid'))

    @test
    def userid_returned_is_the_string_one(self):
        resp = self.showUserByCurrentUser('me')
        self.assertEquals(resp.status_code, 200)
        data = self.fromJson(resp)
        userid = data['userid']
        self.assertTrue(isinstance(userid,basestring))
        self.assertTrue('-' in userid)

    @test
    def user_info_contains_assurance(self):
        current_user = self.controller.getCurrentUser()
        myEmail = current_user.email
        now = time.time()
        Assurance.new(current_user, 'test', current_user, now)
        Assurance.new(current_user, 'test2', current_user, now)
        Assurance.new(current_user, 'test2', current_user, now)
        resp = self.showUserByCurrentUser('me')
        self.assertEquals(resp.status_code, 200)
        data = self.fromJson(resp)
        self.assertTrue(data.has_key('assurances'))
        assurances = data['assurances']
        assurance = assurances['test'][0]
        self.assertEqual(assurance['assurer'], myEmail)
        self.assertEqual(assurance['user'], myEmail)
        self.assertEqual(assurance['timestamp'], now)
        self.assertEqual(assurance['readable_time'], time.asctime(time.gmtime(now)))
        self.assertEqual(len(assurances['test2']),2)

    @test
    def user_info_contains_hash(self):
        current_user = self.controller.getCurrentUser()
        current_user.hash = self.createHash()
        current_user.save()
        resp = self.showUserByCurrentUser('me')
        self.assertEquals(resp.status_code, 200)
        data = self.fromJson(resp)
        self.assertEquals(data['hash'],current_user.hash)

    def _createAssurer(self):
        current_user = self.controller.getCurrentUser()
        Assurance.new(current_user, 'assurer', current_user)
        return current_user

    @test
    def users_with_assurer_assurance_can_get_email_and_digest_for_anyone(self):
        current_user = self._createAssurer()
        targetuser=self.createUserWithCredentials().user
        Assurance.new(targetuser,'test',current_user)
        target = User.getByEmail(self.userCreationEmail)
        resp = self.showUserByCurrentUser(target.userid)
        data = self.fromJson(resp)
        assurances = data['assurances']
        self.assertEquals(assurances['test'][0]['assurer'], current_user.email)
 
    @test
    def users_without_assurer_assurance_cannot_get_email_and_digest_for_anyone(self):
        current_user = self.controller.getCurrentUser()
        targetuser=self.createUserWithCredentials().user
        Assurance.new(targetuser,'test',current_user)
        target = User.getByEmail(self.userCreationEmail)
        with self.assertRaises(ReportedError) as e:
            self.showUserByCurrentUser(target.userid)
        self.assertTrue(e.exception.status,403)

    @test
    def users_with_assurer_assurance_can_get_user_by_email(self):
        self._createAssurer()
        self.setupRandom()
        self.createUserWithCredentials()
        target = User.getByEmail(self.userCreationEmail)
        resp = self.controller.doGetByEmail(target.email)
        self.assertUserResponse(resp)

    @test
    def no_by_email_with_wrong_email(self):
        self._createAssurer()
        self.setupRandom()
        self.createUserWithCredentials()
        target = User.getByEmail(self.userCreationEmail)
        with self.assertRaises(ReportedError) as e:
            self.controller.doGetByEmail('u'+target.email)
        self.assertTrue(e.exception.status,404)

    @test
    def users_without_assurer_assurance_cannot_get_user_by_email(self):
        user = self.createUserWithCredentials()
        self.assertTrue(user is not None)
        target = User.getByEmail(self.userCreationEmail)
        with self.assertRaises(ReportedError) as e:
            self.controller.doGetByEmail(target.email)
        self.assertTrue(e.exception.status,403)

    def createApplication(self):
        redirect_uri = 'https://test.app/redirecturi'
        appid = "app-{0}".format(self.randString)
        self.appsecret = "secret-{0}".format(self.randString)
        application = Application.new(appid, self.appsecret, redirect_uri)
        self.appid = application.appid
        return redirect_uri

    def loginAndGetCode(self):
        redirect_uri = self.createApplication()
        self.controller.interface.set_request_context()
        uri = config.BASE_URL + '/v1/oauth2/auth'
        queryPattern = 'response_type=code&client_id={0}&redirect_uri={1}'
        queryString = queryPattern.format(self.appid, redirect_uri)
        self.controller.interface.set_request_context("/foo?" + queryString)
        resp = AuthProvider(self.controller.interface).auth_interface()
        code = resp.headers['Location'].split("=")[1]
        return code

    def showUserByServer(self, code, userid):
        headers = dict(Authorization='Bearer {0}'.format(code))
        self.controller.interface.set_request_context(headers=headers)
        self.controller.getSession()['auth_user'] = userid, self.appid
        resp = self.controller.doShowUser(userid)
        return self.fromJson(resp)

    def userInfoForServer(self):
        code = self.loginAndGetCode()
        self.controller.logOut()
        data = self.showUserByServer(code, self.cred.user.userid)
        return data 

    @test
    def user_id_shown_to_the_application_differs_from_the_user_id(self):
        data = self.userInfoForServer()
        userid = self.cred.user.userid
        self.assertTrue(userid != data['userid'])

    @test
    def user_id_shown_to_the_application_does_not_change_over_time(self):
        code = self.loginAndGetCode()
        self.controller.logOut()
        data1 = self.showUserByServer(code, self.cred.user.userid)
        data2 = self.showUserByServer(code, self.cred.user.userid)
        self.assertEqual(data1, data2)
