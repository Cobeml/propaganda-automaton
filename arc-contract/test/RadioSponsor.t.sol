// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

import {Test} from "forge-std/Test.sol";
import {RadioSponsor} from "../src/RadioSponsor.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockUSDC is ERC20 {
    constructor() ERC20("Mock USDC", "USDC") {
        _mint(msg.sender, 1000000 * 10**6);
    }
    
    function decimals() public pure override returns (uint8) {
        return 6;
    }
    
    function mint(address to, uint256 amount) external {
        _mint(to, amount);
    }
}

contract RadioSponsorTest is Test {
    RadioSponsor public radioSponsor;
    MockUSDC public usdc;
    
    address public owner = address(0x123);
    address public bidder1 = address(0x456);
    address public bidder2 = address(0x789);
    
    uint256 constant BID_AMOUNT = 1000 * 10**6;
    string constant TRANSCRIPT = "This is a test ad transcript";
    
    function setUp() public {
        vm.startPrank(owner);
        usdc = new MockUSDC();
        radioSponsor = new RadioSponsor(address(usdc));
        vm.stopPrank();
        
        usdc.mint(bidder1, BID_AMOUNT * 10);
        usdc.mint(bidder2, BID_AMOUNT * 10);
        
        vm.prank(bidder1);
        usdc.approve(address(radioSponsor), type(uint256).max);
        
        vm.prank(bidder2);
        usdc.approve(address(radioSponsor), type(uint256).max);
    }
    
    function testSubmitBid() public {
        vm.prank(bidder1);
        radioSponsor.submitBid(BID_AMOUNT, TRANSCRIPT);
        
        RadioSponsor.Bid memory bid = radioSponsor.getBid(1);
        assertEq(bid.bidder, bidder1);
        assertEq(bid.amount, BID_AMOUNT);
        assertEq(bid.transcript, TRANSCRIPT);
        assertEq(uint256(bid.status), uint256(RadioSponsor.BidStatus.Pending));
        assertEq(usdc.balanceOf(address(radioSponsor)), BID_AMOUNT);
    }
    
    function testSubmitBidFailsWithZeroAmount() public {
        vm.prank(bidder1);
        vm.expectRevert("Amount must be greater than 0");
        radioSponsor.submitBid(0, TRANSCRIPT);
    }
    
    function testSubmitBidFailsWithEmptyTranscript() public {
        vm.prank(bidder1);
        vm.expectRevert("Transcript cannot be empty");
        radioSponsor.submitBid(BID_AMOUNT, "");
    }
    
    function testAcceptBid() public {
        vm.prank(bidder1);
        radioSponsor.submitBid(BID_AMOUNT, TRANSCRIPT);
        
        uint256 ownerBalanceBefore = usdc.balanceOf(owner);
        
        vm.prank(owner);
        radioSponsor.acceptBid(1);
        
        RadioSponsor.Bid memory bid = radioSponsor.getBid(1);
        assertEq(uint256(bid.status), uint256(RadioSponsor.BidStatus.Accepted));
        assertEq(usdc.balanceOf(owner), ownerBalanceBefore + BID_AMOUNT);
        assertEq(usdc.balanceOf(address(radioSponsor)), 0);
    }
    
    function testRejectBid() public {
        vm.prank(bidder1);
        radioSponsor.submitBid(BID_AMOUNT, TRANSCRIPT);
        
        uint256 bidderBalanceBefore = usdc.balanceOf(bidder1);
        
        vm.prank(owner);
        radioSponsor.rejectBid(1);
        
        RadioSponsor.Bid memory bid = radioSponsor.getBid(1);
        assertEq(uint256(bid.status), uint256(RadioSponsor.BidStatus.Rejected));
        assertEq(usdc.balanceOf(bidder1), bidderBalanceBefore + BID_AMOUNT);
        assertEq(usdc.balanceOf(address(radioSponsor)), 0);
    }
    
    function testOnlyOwnerCanAcceptBid() public {
        vm.prank(bidder1);
        radioSponsor.submitBid(BID_AMOUNT, TRANSCRIPT);
        
        vm.prank(bidder2);
        vm.expectRevert();
        radioSponsor.acceptBid(1);
    }
    
    function testOnlyOwnerCanRejectBid() public {
        vm.prank(bidder1);
        radioSponsor.submitBid(BID_AMOUNT, TRANSCRIPT);
        
        vm.prank(bidder2);
        vm.expectRevert();
        radioSponsor.rejectBid(1);
    }
    
    function testCannotProcessBidTwice() public {
        vm.prank(bidder1);
        radioSponsor.submitBid(BID_AMOUNT, TRANSCRIPT);
        
        vm.prank(owner);
        radioSponsor.acceptBid(1);
        
        vm.prank(owner);
        vm.expectRevert("Bid already processed");
        radioSponsor.acceptBid(1);
        
        vm.prank(owner);
        vm.expectRevert("Bid already processed");
        radioSponsor.rejectBid(1);
    }
    
    function testGetPendingBidsCount() public {
        assertEq(radioSponsor.getPendingBidsCount(), 0);
        
        vm.prank(bidder1);
        radioSponsor.submitBid(BID_AMOUNT, TRANSCRIPT);
        assertEq(radioSponsor.getPendingBidsCount(), 1);
        
        vm.prank(bidder2);
        radioSponsor.submitBid(BID_AMOUNT, "Another transcript");
        assertEq(radioSponsor.getPendingBidsCount(), 2);
        
        vm.prank(owner);
        radioSponsor.acceptBid(1);
        assertEq(radioSponsor.getPendingBidsCount(), 1);
        
        vm.prank(owner);
        radioSponsor.rejectBid(2);
        assertEq(radioSponsor.getPendingBidsCount(), 0);
    }
    
    function testMultipleBids() public {
        vm.prank(bidder1);
        radioSponsor.submitBid(BID_AMOUNT, TRANSCRIPT);
        
        vm.prank(bidder2);
        radioSponsor.submitBid(BID_AMOUNT * 2, "Second transcript");
        
        assertEq(radioSponsor.nextBidId(), 3);
        assertEq(usdc.balanceOf(address(radioSponsor)), BID_AMOUNT * 3);
        
        RadioSponsor.Bid memory bid1 = radioSponsor.getBid(1);
        RadioSponsor.Bid memory bid2 = radioSponsor.getBid(2);
        
        assertEq(bid1.bidder, bidder1);
        assertEq(bid2.bidder, bidder2);
        assertEq(bid1.amount, BID_AMOUNT);
        assertEq(bid2.amount, BID_AMOUNT * 2);
    }
}